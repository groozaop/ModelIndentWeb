from django.contrib import admin
from .models import (
    ItemGroup, Item, Trade, Instructor,
    DemandNote, DemandItem,
    ModelIndent, GPR, ConsumableRegister,
    UltimateQuery, UltimateQueryItem
)
import xlwt
import io
from django.http import FileResponse


# ─── Item Group ──────────────────────────────────────────────────────────────

@admin.register(ItemGroup)
class ItemGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'item_count')
    search_fields = ('name',)

    @admin.display(description='No. of Items')
    def item_count(self, obj):
        return obj.items.count()


# ─── Item ────────────────────────────────────────────────────────────────────

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('item_code', 'item_name', 'item_unit', 'est_price', 'group')
    search_fields = ('item_name', 'item_code')
    list_filter = ('group', 'item_unit')
    list_per_page = 25


# ─── Trade ───────────────────────────────────────────────────────────────────

@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ('trade_name', 'total_semesters', 'instructor_count')
    search_fields = ('trade_name',)

    @admin.display(description='No. of Instructors')
    def instructor_count(self, obj):
        return obj.instructors.count()


# ─── Instructor ──────────────────────────────────────────────────────────────

@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ('name', 'trade', 'user')
    search_fields = ('name', 'user__username')
    list_filter = ('trade',)
    autocomplete_fields = ('user',)


# ─── Demand Note + Inline Items ──────────────────────────────────────────────

class DemandItemInline(admin.TabularInline):
    model = DemandItem
    extra = 1
    autocomplete_fields = ('item',)


@admin.register(DemandNote)
class DemandNoteAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'instructor', 'trade',
        'semester_no', 'financial_year', 'status',
        'total_items', 'created_at', 'submitted_at'
    )
    list_filter = ('status', 'trade', 'financial_year')
    search_fields = ('instructor__name',)
    list_editable = ('status',)
    list_per_page = 30
    date_hierarchy = 'created_at'
    inlines = [DemandItemInline]


@admin.register(DemandItem)
class DemandItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'demand_note', 'item', 'quantity_required')
    list_filter = ('demand_note__status', 'demand_note__financial_year')
    search_fields = ('item__item_name',)


# ─── Model Indent (Legacy) ──────────────────────────────────────────────────

@admin.register(ModelIndent)
class ModelIndentAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'instructor', 'item', 'trade',
        'quantity_required', 'semester_no',
        'financial_year', 'status', 'created_at'
    )
    list_filter = ('status', 'trade', 'financial_year')
    search_fields = ('item__item_name', 'instructor__name')
    list_editable = ('status',)
    list_per_page = 30
    date_hierarchy = 'created_at'
    autocomplete_fields = ('instructor', 'item')


# ─── GPR ─────────────────────────────────────────────────────────────────────

@admin.register(GPR)
class GPRAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'inward_date', 'supplier_name',
        'item', 'item_qty', 'bill_no', 'financial_year'
    )
    list_filter = ('financial_year', 'supplier_name')
    search_fields = ('item__item_name', 'supplier_name', 'bill_no')
    date_hierarchy = 'inward_date'
    list_per_page = 25


# ─── CR ──────────────────────────────────────────────────────────────────────

@admin.register(ConsumableRegister)
class ConsumableRegisterAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'item', 'instructor', 'trade',
        'inward_date', 'opening_bal', 'out_qty', 'current_bal'
    )
    list_filter = ('trade', 'instructor')
    search_fields = ('item__item_name', 'instructor__name')
    date_hierarchy = 'inward_date'
    readonly_fields = ('current_bal',)
    list_per_page = 25


# ─── Ultimate Query (Procurement Batch) ──────────────────────────────────────

@admin.action(description='Export Consolidated Matrix (.xls)')
def export_to_excel(modeladmin, request, queryset):
    """Admin action to reuse the established matrix export logic."""
    if queryset.count() != 1:
        modeladmin.message_user(request, "Please select exactly one query to export.", level='error')
        return
        
    # Lazy import to avoid circular dependency
    from .views import export_ultimate_query_xls
    return export_ultimate_query_xls(request, queryset.first().pk)


@admin.register(UltimateQuery)
class UltimateQueryAdmin(admin.ModelAdmin):
    list_display = ('query_no', 'financial_year', 'created_at', 'is_purchased')
    list_filter = ('financial_year', 'is_purchased')
    search_fields = ('query_no',)
    actions = [export_to_excel]
