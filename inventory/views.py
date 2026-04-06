from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group, User
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.db.models import Sum
from django.http import JsonResponse
from django.utils import timezone

from .models import (
    DemandNote, DemandItem, Item, GPR, ConsumableRegister,
    Instructor, Trade, FINANCIAL_YEAR_CHOICES,
    UltimateQuery, UltimateQueryItem, ItemGroup,
)
from django.db.models import Q
import xlwt
import io
import traceback
from django.http import FileResponse, HttpResponse
from .forms import (
    DemandNoteForm, DemandItemFormSet,
    EditDemandNoteForm, UserUpdateForm,
    GPRForm, AllocateToCRForm,
)


# ─── Utility checks ─────────────────────────────────────────────────────────

def is_instructor(user):
    return user.groups.filter(name='Instructors').exists()

def is_storekeeper(user):
    return user.groups.filter(name='StoreKeepers').exists()

def is_instructor_or_super(user):
    return user.is_superuser or is_instructor(user)

def is_storekeeper_or_super(user):
    return user.is_superuser or is_storekeeper(user)

# ─── User Profile & Password ────────────────────────────────────────────────

@login_required
def profile(request):
    """View for users to update their profile details."""
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('inventory:profile')
    else:
        form = UserUpdateForm(instance=request.user)
    
    return render(request, 'inventory/profile.html', {
        'form': form
    })

@login_required
def change_password(request):
    """View to allow users to change their password."""
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            # Keep the user logged in after password change
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('inventory:profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(user=request.user)
    
    return render(request, 'inventory/change_password.html', {
        'form': form
    })


# ─── Dashboard ───────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    context = {
        'total_items': Item.objects.count(),
        'pending_demands': DemandNote.objects.filter(status='SUBMITTED').count(),
        'total_gpr': GPR.objects.count(),
    }

    if hasattr(request.user, 'instructor_profile'):
        instructor = request.user.instructor_profile
        context['my_demands'] = DemandNote.objects.filter(
            instructor=instructor
        ).prefetch_related('items__item')[:10]
        context['draft_count'] = DemandNote.objects.filter(
            instructor=instructor, status='DRAFT'
        ).count()

    return render(request, 'inventory/dashboard.html', context)


# ═══════════════════════════════════════════════════════════════════════════════
#  INSTRUCTOR: Demand Note CRUD
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
@user_passes_test(is_instructor_or_super, login_url='/accounts/login/')
def create_demand(request):
    """Create a new Demand Note with multiple items (saved as DRAFT)."""
    instructor = get_object_or_404(Instructor, user=request.user)

    if request.method == 'POST':
        form = DemandNoteForm(request.POST)
        formset = DemandItemFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            demand = form.save(commit=False)
            demand.instructor = instructor
            demand.trade = instructor.trade
            demand.status = 'DRAFT'
            demand.save()

            formset.instance = demand
            formset.save()

            messages.success(
                request,
                f'Demand Note DN-{demand.pk:04d} saved as Draft '
                f'with {demand.total_items} item(s).'
            )
            return redirect('inventory:view_demand', demand_id=demand.pk)
    else:
        form = DemandNoteForm()
        formset = DemandItemFormSet()

    return render(request, 'inventory/create_demand.html', {
        'form': form,
        'formset': formset,
    })


@login_required
@user_passes_test(is_instructor_or_super, login_url='/accounts/login/')
def edit_demand(request, demand_id):
    """Edit a DRAFT demand note (add/remove/change items)."""
    instructor = get_object_or_404(Instructor, user=request.user)
    demand = get_object_or_404(DemandNote, pk=demand_id, instructor=instructor)

    if not demand.is_editable:
        messages.error(request, 'This demand has already been submitted and cannot be edited.')
        return redirect('inventory:view_demand', demand_id=demand.pk)

    if request.method == 'POST':
        form = DemandNoteForm(request.POST, instance=demand)
        formset = DemandItemFormSet(request.POST, instance=demand)

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, f'Demand Note DN-{demand.pk:04d} updated.')
            return redirect('inventory:view_demand', demand_id=demand.pk)
    else:
        form = DemandNoteForm(instance=demand)
        formset = DemandItemFormSet(instance=demand)

    return render(request, 'inventory/edit_demand.html', {
        'form': form,
        'formset': formset,
        'demand': demand,
    })


@login_required
@user_passes_test(is_instructor_or_super, login_url='/accounts/login/')
def view_demand(request, demand_id):
    """View a demand note (read-only if submitted)."""
    instructor = get_object_or_404(Instructor, user=request.user)
    demand = get_object_or_404(DemandNote, pk=demand_id, instructor=instructor)
    items = demand.items.select_related('item', 'item__group')

    return render(request, 'inventory/view_demand.html', {
        'demand': demand,
        'items': items,
    })


@login_required
@user_passes_test(is_instructor_or_super, login_url='/accounts/login/')
def submit_demand(request, demand_id):
    """Submit a DRAFT demand to the storekeeper (locks it)."""
    instructor = get_object_or_404(Instructor, user=request.user)
    demand = get_object_or_404(DemandNote, pk=demand_id, instructor=instructor)

    if demand.status != 'DRAFT':
        messages.error(request, 'This demand has already been submitted.')
        return redirect('inventory:view_demand', demand_id=demand.pk)

    if demand.total_items == 0:
        messages.error(request, 'Cannot submit a demand with no items. Add items first.')
        return redirect('inventory:edit_demand', demand_id=demand.pk)

    if request.method == 'POST':
        demand.status = 'SUBMITTED'
        demand.submitted_at = timezone.now()
        demand.save()
        messages.success(
            request,
            f'Demand Note DN-{demand.pk:04d} submitted to Storekeeper! '
            f'It is now locked for editing.'
        )
        return redirect('inventory:my_demands')

    return redirect('inventory:view_demand', demand_id=demand.pk)


@login_required
@user_passes_test(is_instructor_or_super, login_url='/accounts/login/')
def delete_demand(request, demand_id):
    """Delete a DRAFT demand note."""
    instructor = get_object_or_404(Instructor, user=request.user)
    demand = get_object_or_404(DemandNote, pk=demand_id, instructor=instructor)

    if not demand.is_editable:
        messages.error(request, 'Cannot delete a submitted demand.')
        return redirect('inventory:my_demands')

    if request.method == 'POST':
        demand.delete()
        messages.success(request, f'Demand Note #{demand_id} deleted.')
    return redirect('inventory:my_demands')


@login_required
@user_passes_test(is_instructor_or_super, login_url='/accounts/login/')
def my_demands(request):
    """Instructor's demand history (drafts + submitted)."""
    instructor = get_object_or_404(Instructor, user=request.user)
    demands = DemandNote.objects.filter(
        instructor=instructor
    ).prefetch_related('items__item')

    status = request.GET.get('status')
    fy = request.GET.get('financial_year')
    if status:
        demands = demands.filter(status=status)
    if fy:
        demands = demands.filter(financial_year=fy)

    return render(request, 'inventory/my_demands.html', {
        'demands': demands,
        'status_choices': DemandNote.STATUS_CHOICES,
        'financial_years': FINANCIAL_YEAR_CHOICES,
        'selected_status': status,
        'selected_fy': fy,
    })


# ═══════════════════════════════════════════════════════════════════════════════
#  STOREKEEPER: View & manage ALL submitted demands
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
@user_passes_test(is_storekeeper_or_super, login_url='/accounts/login/')
def all_demands(request):
    """StoreKeeper sees ALL submitted (and beyond) demand notes."""
    demands = DemandNote.objects.filter(
        status__in=['SUBMITTED', 'MERGED', 'PURCHASED', 'ISSUED']
    ).select_related('instructor', 'trade').prefetch_related('items__item')

    fy = request.GET.get('financial_year')
    status = request.GET.get('status')
    trade_id = request.GET.get('trade')
    if fy:
        demands = demands.filter(financial_year=fy)
    if status:
        demands = demands.filter(status=status)
    if trade_id:
        demands = demands.filter(trade_id=trade_id)

    return render(request, 'inventory/all_demands.html', {
        'demands': demands,
        'financial_years': FINANCIAL_YEAR_CHOICES,
        'status_choices': [c for c in DemandNote.STATUS_CHOICES if c[0] != 'DRAFT'],
        'trades': Trade.objects.all(),
        'selected_fy': fy,
        'selected_status': status,
        'selected_trade': trade_id,
    })


@login_required
@user_passes_test(is_storekeeper_or_super, login_url='/accounts/login/')
def store_view_demand(request, demand_id):
    """StoreKeeper view of a demand note (with edit controls)."""
    demand = get_object_or_404(DemandNote, pk=demand_id)

    if demand.status == 'DRAFT':
        messages.error(request, 'This demand has not been submitted yet.')
        return redirect('inventory:all_demands')

    items = demand.items.select_related('item', 'item__group')

    if request.method == 'POST':
        form = EditDemandNoteForm(request.POST, instance=demand)
        if form.is_valid():
            form.save()
            messages.success(request, f'Demand Note DN-{demand.pk:04d} updated.')
            return redirect('inventory:store_view_demand', demand_id=demand.pk)
    else:
        form = EditDemandNoteForm(instance=demand)

    return render(request, 'inventory/store_view_demand.html', {
        'demand': demand,
        'items': items,
        'form': form,
    })


# ─── Item Data API (for JS unit lookup) ──────────────────────────────────────

@login_required
def item_data_json(request):
    """Return item data as JSON for JS consumption (unit, price)."""
    items = Item.objects.select_related('group').all()
    data = {}
    for item in items:
        data[item.item_code] = {
            'unit': item.item_unit,
            'price': float(item.est_price),
            'name': item.item_name,
            'group': item.group.name if item.group else '',
        }
    return JsonResponse(data)


@login_required
def search_items(request):
    """
    Enhanced server-side search for items.
    Splits query by spaces and matches all words (AND logic).
    Supports regex patterns if valid.
    """
    query = request.GET.get('q', '').strip()
    results = []
    
    if len(query) >= 2:
        words = query.split()
        q_obj = Q()
        for word in words:
            q_obj &= (Q(item_name__icontains=word) | Q(item_code__icontains=word))
            
        try:
            # Try applying as regex if the user provides a special pattern
            items = Item.objects.filter(
                q_obj | Q(item_name__iregex=query)
            ).select_related('group')[:25]
        except Exception:
            # Fallback to smart word matching
            items = Item.objects.filter(q_obj).select_related('group')[:25]
            
        for item in items:
            results.append({
                'id': item.pk,
                'text': f"{item.item_name} [{item.item_code}]",
                'unit': item.item_unit,
                'price': float(item.est_price),
                'group': item.group.name if item.group else 'No Category'
            })
            
    return JsonResponse({'results': results})


# ─── StoreKeeper: Merge Demand (Checkbox Selection) ─────────────────────────

@login_required
@user_passes_test(is_storekeeper_or_super, login_url='/accounts/login/')
def merge_demand(request):
    """
    Merge preview page.
    POST: accepts specific demand note IDs.
    GET: previews ALL currently 'SUBMITTED' demands.
    Aggregates their items by item_code.
    """
    merged_data = []
    total_estimated_cost = 0
    selected_ids = []
    selected_demands = []

    if request.method == 'POST':
        selected_ids = request.POST.getlist('demand_ids')
    else:
        # For GET (sidebar link), default to all SUBMITTED demands
        selected_ids = list(DemandNote.objects.filter(status='SUBMITTED').values_list('pk', flat=True))

    if selected_ids:
        selected_demands = DemandNote.objects.filter(
            pk__in=selected_ids, status='SUBMITTED'
        ).select_related('instructor', 'trade')

        merged_data = (
            DemandItem.objects
            .filter(demand_note__pk__in=selected_ids, demand_note__status='SUBMITTED')
            .values(
                'item__item_code',
                'item__item_name',
                'item__item_unit',
                'item__est_price',
                'item__group__name',
            )
            .annotate(total_qty=Sum('quantity_required'))
            .order_by('item__group__name', 'item__item_name')
        )

        for row in merged_data:
            row['estimated_cost'] = row['total_qty'] * row['item__est_price']
            total_estimated_cost += row['estimated_cost']

    return render(request, 'inventory/merge_demand.html', {
        'merged_data': merged_data,
        'total_estimated_cost': total_estimated_cost,
        'selected_ids': [str(sid) for sid in selected_ids],
        'selected_demands': selected_demands,
    })


@login_required
@user_passes_test(is_storekeeper_or_super, login_url='/accounts/login/')
def mark_merged(request):
    """Mark the selected SUBMITTED demands as MERGED and create an Ultimate Query entity."""
    if request.method == 'POST':
        demand_ids = request.POST.getlist('demand_ids')
        if demand_ids:
            demands = DemandNote.objects.filter(pk__in=demand_ids, status='SUBMITTED')
            
            if not demands.exists():
                messages.warning(request, "Selected demands are no longer eligible for merge.")
                return redirect('inventory:all_demands')

            # Aggregate items before status update
            merged_items = (
                DemandItem.objects
                .filter(demand_note__pk__in=demand_ids)
                .values('item')
                .annotate(total_qty=Sum('quantity_required'))
            )

            # Create UltimateQuery with auto-generated ID
            import datetime
            today = datetime.datetime.now()
            year_str = today.strftime('%Y')
            uq_count = UltimateQuery.objects.filter(created_at__year=today.year).count() + 1
            query_no = f"UQ-{year_str}-{uq_count:04d}"
            
            # Use most common FY
            fy = demands.first().financial_year
            
            uq = UltimateQuery.objects.create(
                query_no=query_no,
                financial_year=fy
            )
            uq.demand_notes.set(demands)
            
            # Create consolidated items
            for row in merged_items:
                item_obj = Item.objects.get(pk=row['item'])
                UltimateQueryItem.objects.create(
                    ultimate_query=uq,
                    item=item_obj,
                    total_quantity=row['total_qty'],
                    estimated_rate=item_obj.est_price
                )

            # Mark demands as merged
            count = demands.update(status='MERGED')
            messages.success(request, f'Consolidated into {query_no}. {count} demand(s) processed.')
            return redirect('inventory:ultimate_query_detail', uq_id=uq.pk)
        else:
            messages.warning(request, 'No demands selected.')
    return redirect('inventory:all_demands')


@login_required
@user_passes_test(is_storekeeper_or_super, login_url='/accounts/login/')
def ultimate_query_list(request):
    queries = UltimateQuery.objects.prefetch_related('items').order_by('-created_at')
    return render(request, 'inventory/ultimate_query_list.html', {'queries': queries})


@login_required
@user_passes_test(is_storekeeper_or_super, login_url='/accounts/login/')
def ultimate_query_detail(request, uq_id):
    """Detail view for Ultimate Query with instructor distribution matrix."""
    query = get_object_or_404(UltimateQuery, pk=uq_id)
    uq_items = query.items.select_related('item', 'item__group').order_by('item__item_name')
    total_cost = sum(item.total_estimated_cost for item in uq_items)
    
    # Get all source demand notes and their instructors
    source_demands = query.demand_notes.select_related('instructor', 'trade')
    
    # Get unique instructors (preserving order)
    instructors = []
    seen_pks = set()
    for dn in source_demands:
        if dn.instructor.pk not in seen_pks:
            instructors.append(dn.instructor)
            seen_pks.add(dn.instructor.pk)

    # Build matrix: mapping (item_code, instructor_pk) -> quantity
    # We pre-calculate to avoid nested queries in loop
    matrix_data = {}
    source_items = DemandItem.objects.filter(demand_note__in=source_demands)
    for di in source_items:
        key = (di.item.item_code, di.demand_note.instructor.pk)
        matrix_data[key] = matrix_data.get(key, 0) + di.quantity_required

    # Build display-friendly matrix rows
    matrix_rows = []
    for uq_item in uq_items:
        row = {
            'item': uq_item.item,
            'total_qty': uq_item.total_quantity,
            'instructor_cols': []
        }
        for inst in instructors:
            qty = matrix_data.get((uq_item.item.item_code, inst.pk), 0)
            row['instructor_cols'].append(qty)
        matrix_rows.append(row)

    return render(request, 'inventory/ultimate_query_detail.html', {
        'query': query,
        'items': uq_items,
        'total_cost': total_cost,
        'instructors': instructors,
        'matrix_rows': matrix_rows
    })


# ─── StoreKeeper: GPR ────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_storekeeper_or_super, login_url='/accounts/login/')
def add_gpr(request):
    if request.method == 'POST':
        form = GPRForm(request.POST)
        if form.is_valid():
            gpr = form.save()
            messages.success(request, f'GPR entry for "{gpr.item.item_name}" added.')
            return redirect('inventory:allocate_cr', gpr_id=gpr.pk)
    else:
        form = GPRForm()
    return render(request, 'inventory/add_gpr.html', {'form': form})


@login_required
@user_passes_test(is_storekeeper_or_super, login_url='/accounts/login/')
def gpr_list(request):
    entries = GPR.objects.select_related('item').all()
    fy = request.GET.get('financial_year')
    if fy:
        entries = entries.filter(financial_year=fy)

    # Annotate each GPR entry with allocated and outstanding quantities
    enriched = []
    for gpr in entries:
        allocated = ConsumableRegister.objects.filter(
            item=gpr.item,
            inward_date=gpr.inward_date
        ).aggregate(total=Sum('opening_bal'))['total'] or 0
        outstanding = gpr.item_qty - allocated
        enriched.append({
            'gpr': gpr,
            'allocated_qty': allocated,
            'outstanding_qty': outstanding,
            'is_fully_allocated': outstanding <= 0,
        })

    # Summary counts — computed in Python, not in template
    fully_allocated_count = sum(1 for row in enriched if row['is_fully_allocated'])
    pending_count = len(enriched) - fully_allocated_count

    return render(request, 'inventory/gpr_list.html', {
        'enriched': enriched,
        'financial_years': FINANCIAL_YEAR_CHOICES,
        'selected_fy': fy,
        'total_count': len(enriched),
        'pending_count': pending_count,
        'fully_allocated_count': fully_allocated_count,
    })


# ─── StoreKeeper: Allocate GPR → CR ─────────────────────────────────────────

@login_required
@user_passes_test(is_storekeeper_or_super, login_url='/accounts/login/')
def allocate_cr(request, gpr_id):
    gpr = get_object_or_404(GPR, pk=gpr_id)

    allocated = ConsumableRegister.objects.filter(
        item=gpr.item, inward_date=gpr.inward_date
    ).aggregate(total=Sum('opening_bal'))['total'] or 0
    remaining_qty = gpr.item_qty - allocated

    if request.method == 'POST':
        form = AllocateToCRForm(request.POST, item=gpr.item)
        if form.is_valid():
            cr = form.save(commit=False)
            cr.item = gpr.item
            cr.trade = cr.instructor.trade
            cr.inward_date = gpr.inward_date
            if cr.opening_bal > remaining_qty:
                messages.error(request, f'Cannot allocate {cr.opening_bal}. Only {remaining_qty} remaining.')
            else:
                cr.save()
                messages.success(request, f'Allocated {cr.opening_bal} to {cr.instructor.name}.')
                return redirect('inventory:allocate_cr', gpr_id=gpr.pk)
    else:
        form = AllocateToCRForm(item=gpr.item)

    allocations = ConsumableRegister.objects.filter(
        item=gpr.item, inward_date=gpr.inward_date
    ).select_related('instructor', 'trade')

    return render(request, 'inventory/allocate_cr.html', {
        'gpr': gpr, 'form': form,
        'remaining_qty': remaining_qty, 'allocations': allocations,
    })


@login_required
def cr_list(request):
    entries = ConsumableRegister.objects.select_related('item', 'instructor', 'trade').order_by('-inward_date')

    # --- Filters ---
    instructor_id = request.GET.get('instructor')
    item_code = request.GET.get('item')
    trade_id = request.GET.get('trade')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if instructor_id:
        entries = entries.filter(instructor_id=instructor_id)
    if item_code:
        entries = entries.filter(item__item_code=item_code)
    if trade_id:
        entries = entries.filter(trade_id=trade_id)
    if date_from:
        entries = entries.filter(inward_date__gte=date_from)
    if date_to:
        entries = entries.filter(inward_date__lte=date_to)

    # Populate dropdowns — items scoped to only what's actually in CR
    all_instructors = Instructor.objects.select_related('trade').order_by('name')
    cr_item_codes = ConsumableRegister.objects.values_list('item__item_code', flat=True).distinct()
    all_items = Item.objects.filter(item_code__in=cr_item_codes).order_by('item_name')
    all_trades = Trade.objects.order_by('trade_name')

    return render(request, 'inventory/cr_list.html', {
        'entries': entries,
        'all_instructors': all_instructors,
        'all_items': all_items,
        'all_trades': all_trades,
        # Keep selected values to repopulate form
        'sel_instructor': instructor_id,
        'sel_item': item_code,
        'sel_trade': trade_id,
        'sel_date_from': date_from,
        'sel_date_to': date_to,
    })


@login_required
@user_passes_test(is_storekeeper_or_super, login_url='/accounts/login/')
def export_ultimate_query_xls(request, uq_id):
    """Generates a professional matrix with robust debugging wrap."""
    try:
        query = get_object_or_404(UltimateQuery, pk=uq_id)
        uq_items = query.items.select_related('item', 'item__group').order_by('item__item_name')
        
        # Get all source demand notes and their instructors
        source_demands = query.demand_notes.select_related('instructor', 'trade').all()
        
        # Get unique instructors (preserving order)
        instructors = []
        seen_pks = set()
        for dn in source_demands:
            if dn.instructor.pk not in seen_pks:
                instructors.append(dn.instructor)
                seen_pks.add(dn.instructor.pk)

        # Matrix data pre-calculation
        matrix_data = {}
        source_items = DemandItem.objects.filter(demand_note__in=source_demands)
        for di in source_items:
            key = (di.item.item_code, di.demand_note.instructor.pk)
            matrix_data[key] = matrix_data.get(key, 0) + di.quantity_required

        # Initialize XLS Workbook
        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet('Consolidated Requirement')

        # Formatting Styles
        font_bold = xlwt.Font()
        font_bold.bold = True
        style_header = xlwt.XFStyle()
        style_header.font = font_bold
        
        # Write Meta Header
        ws.write(0, 0, f"INSTITUTIONAL PROCUREMENT MATRIX: {query.query_no}", style_header)
        ws.write(1, 0, f"Session: {query.financial_year}")
        
        # Define and Write Column Headers
        headers = ['SR', 'CODE', 'ITEM DESCRIPTION', 'CATEGORY', 'UNIT', 'TOTAL']
        for inst in instructors:
            # Safer access to trade properties
            t_code = getattr(inst.trade, 'id', 'x')
            headers.append(f"{inst.name.upper()} ({t_code})")
            
        for i, header in enumerate(headers):
            ws.write(3, i, header, style_header)

        # Write Item Data
        for idx, uq_item in enumerate(uq_items, 1):
            row = 3 + idx
            ws.write(row, 0, idx)
            ws.write(row, 1, uq_item.item.item_code)
            ws.write(row, 2, uq_item.item.item_name)
            ws.write(row, 3, uq_item.item.group.name)
            ws.write(row, 4, uq_item.item.item_unit)
            ws.write(row, 5, float(uq_item.total_quantity))
            
            # Instructor breakdowns
            for col_offset, inst in enumerate(instructors):
                qty = matrix_data.get((uq_item.item.item_code, inst.pk), 0)
                ws.write(row, 6 + col_offset, float(qty) if qty > 0 else 0)

        # Stream to FileResponse
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        filename = f"Requisition_Matrix_{query.pk}.xls"
        return FileResponse(
            buffer, 
            as_attachment=True, 
            filename=filename, 
            content_type='application/vnd.ms-excel'
        )
    except Exception as e:
        # Emergency diagnostic response
        error_msg = f"Excel Export Failure: {str(e)}\n\n{traceback.format_exc()}"
        return HttpResponse(error_msg, content_type="text/plain")
