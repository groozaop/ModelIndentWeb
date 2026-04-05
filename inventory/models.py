from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


# ─── Shared Constants ────────────────────────────────────────────────────────

FINANCIAL_YEAR_CHOICES = []
for _year in range(2020, 2036):
    _fy = f"{_year}-{_year + 1}"
    FINANCIAL_YEAR_CHOICES.append((_fy, _fy))


# ─── Core Models ─────────────────────────────────────────────────────────────

class ItemGroup(models.Model):
    """Groups/Categories for inventory items."""
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Item Group'
        verbose_name_plural = 'Item Groups'

    def __str__(self):
        return self.name


class Item(models.Model):
    """Individual inventory items with pricing and group association."""
    item_code = models.CharField(max_length=50, primary_key=True)
    item_name = models.CharField(max_length=255)
    item_unit = models.CharField(
        max_length=50,
        help_text="Unit of measurement (e.g., Nos, Kg, Ltr, Mtr)"
    )
    est_price = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Estimated Price'
    )
    group = models.ForeignKey(
        ItemGroup,
        on_delete=models.CASCADE,
        related_name='items'
    )

    class Meta:
        ordering = ['item_name']
        verbose_name = 'Item'
        verbose_name_plural = 'Items'

    def __str__(self):
        return f"{self.item_code} - {self.item_name}"


class Trade(models.Model):
    """Trades/Departments offered by the institution."""
    trade_name = models.CharField(max_length=200, unique=True)
    total_semesters = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Total number of semesters in this trade"
    )

    class Meta:
        ordering = ['trade_name']

    def __str__(self):
        return self.trade_name


class Instructor(models.Model):
    """Instructor profiles linked to a trade and user account."""
    name = models.CharField(max_length=200)
    trade = models.ForeignKey(
        Trade,
        on_delete=models.CASCADE,
        related_name='instructors'
    )
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='instructor_profile'
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.trade.trade_name})"


# ─── Demand Note System (Parent-Child) ───────────────────────────────────────

class DemandNote(models.Model):
    """
    A demand document created by an instructor containing multiple items.
    Workflow: DRAFT → SUBMITTED → MERGED → PURCHASED → ISSUED
    """
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('MERGED', 'Merged'),
        ('PURCHASED', 'Purchased'),
        ('ISSUED', 'Issued'),
    ]

    instructor = models.ForeignKey(
        Instructor,
        on_delete=models.CASCADE,
        related_name='demand_notes'
    )
    trade = models.ForeignKey(
        Trade,
        on_delete=models.CASCADE,
        related_name='demand_notes'
    )
    semester_no = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Semester Number'
    )
    financial_year = models.CharField(
        max_length=9,
        choices=FINANCIAL_YEAR_CHOICES,
        help_text="e.g., 2025-2026"
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='DRAFT'
    )
    remarks = models.TextField(blank=True, null=True, help_text="Optional notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Demand Note'
        verbose_name_plural = 'Demand Notes'

    @property
    def is_editable(self):
        return self.status == 'DRAFT'

    @property
    def total_items(self):
        return self.items.count()

    @property
    def total_estimated_cost(self):
        total = 0
        for di in self.items.select_related('item'):
            total += di.quantity_required * di.item.est_price
        return total

    def __str__(self):
        return (
            f"DN-{self.pk:04d} | {self.instructor.name} | "
            f"{self.financial_year} | {self.get_status_display()}"
        )


class DemandItem(models.Model):
    """Individual line item within a DemandNote."""
    demand_note = models.ForeignKey(
        DemandNote,
        on_delete=models.CASCADE,
        related_name='items'
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name='demand_items'
    )
    quantity_required = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )

    class Meta:
        ordering = ['id']
        verbose_name = 'Demand Item'
        verbose_name_plural = 'Demand Items'
        unique_together = ['demand_note', 'item']  # No duplicate items in same note

    @property
    def estimated_cost(self):
        return self.quantity_required * self.item.est_price

    def __str__(self):
        return f"{self.item.item_name} x{self.quantity_required}"


class ModelIndent(models.Model):
    """
    Demand/Indent raised by instructors for items.
    Tracks status from PENDING through PURCHASED to ISSUED.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('MERGED', 'Merged'),
        ('PURCHASED', 'Purchased'),
        ('ISSUED', 'Issued'),
    ]

    instructor = models.ForeignKey(
        Instructor,
        on_delete=models.CASCADE,
        related_name='indents'
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name='indents'
    )
    trade = models.ForeignKey(
        Trade,
        on_delete=models.CASCADE,
        related_name='indents'
    )
    quantity_required = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    semester_no = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Semester Number'
    )
    financial_year = models.CharField(
        max_length=9,
        choices=FINANCIAL_YEAR_CHOICES,
        help_text="e.g., 2025-2026"
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Model Indent'
        verbose_name_plural = 'Model Indents'

    def __str__(self):
        return (
            f"Indent #{self.pk} | {self.item.item_name} x{self.quantity_required} "
            f"| {self.instructor.name} | {self.get_status_display()}"
        )


class GPR(models.Model):
    """
    Goods Purchase Register — records inward stock from suppliers.
    """
    inward_date = models.DateField()
    supplier_name = models.CharField(max_length=300)
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name='gpr_entries'
    )
    item_qty = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Quantity Received'
    )
    bill_no = models.CharField(max_length=100, verbose_name='Bill Number')
    financial_year = models.CharField(
        max_length=9,
        choices=FINANCIAL_YEAR_CHOICES,
        help_text="e.g., 2025-2026"
    )
    gpr_no = models.CharField(max_length=100, default='GPR-000', verbose_name='GPR Number')
    # Register/Ledger indexing (mapping to CR)
    register_no = models.PositiveIntegerField(default=1, verbose_name='Register No')
    page_no = models.PositiveIntegerField(default=1, verbose_name='Page No')
    item_no = models.PositiveIntegerField(default=1, verbose_name='Item Index')
    sub_entry = models.PositiveIntegerField(default=1, verbose_name='Sub Entry')

    class Meta:
        ordering = ['-inward_date', 'register_no', 'page_no', 'item_no', 'sub_entry']
        verbose_name = 'Goods Purchase Register (GPR)'
        verbose_name_plural = 'Goods Purchase Register (GPR)'

    @property
    def gpr_reference(self):
        # As requested, renamed from GPR to CR prefix for consistency with CR indexing
        return f"CR-{self.register_no}/{self.page_no}/{self.item_no}/{self.sub_entry}"

    def __str__(self):
        return (
            f"GPR | {self.item.item_name} x{self.item_qty} "
            f"from {self.supplier_name} on {self.inward_date}"
        )


class ConsumableRegister(models.Model):
    """
    Consumable Register (CR) — tracks item issuance to instructors.
    """
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name='cr_entries'
    )
    instructor = models.ForeignKey(
        Instructor,
        on_delete=models.CASCADE,
        related_name='cr_entries'
    )
    trade = models.ForeignKey(
        Trade,
        on_delete=models.CASCADE,
        related_name='cr_entries'
    )
    inward_date = models.DateField()
    opening_bal = models.PositiveIntegerField(
        default=0,
        verbose_name='Opening Balance'
    )
    out_qty = models.PositiveIntegerField(
        default=0,
        verbose_name='Quantity Issued'
    )
    current_bal = models.PositiveIntegerField(
        default=0,
        verbose_name='Current Balance'
    )
    # Register/Ledger indexing (e.g., CR-1/5/42/2)
    register_no = models.PositiveIntegerField(default=1, verbose_name='CR Register No')
    page_no = models.PositiveIntegerField(default=1, verbose_name='Page No')
    item_no = models.PositiveIntegerField(default=1, verbose_name='Item Index')
    sub_entry = models.PositiveIntegerField(default=1, verbose_name='Sub Entry')

    class Meta:
        ordering = ['-inward_date', 'register_no', 'page_no', 'item_no', 'sub_entry']
        verbose_name = 'Consumable Register (CR)'
        verbose_name_plural = 'Consumable Register (CR)'

    @property
    def cr_reference(self):
        # Format: CR-1/5/42/2
        return f"CR-{self.register_no}/{self.page_no}/{self.item_no}/{self.sub_entry}"

    def save(self, *args, **kwargs):
        """Auto-calculate current balance on save."""
        self.current_bal = self.opening_bal - self.out_qty
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"CR | {self.item.item_name} → {self.instructor.name} "
            f"| Bal: {self.current_bal}"
        )


# ─── Ultimate Query System ───────────────────────────────────────────────────

class UltimateQuery(models.Model):
    """
    Represents a finalized, merged set of requirements derived from multiple DemandNotes.
    Acts as the 'Ultimate Query' entity for procurement.
    """
    query_no = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Query Number",
        help_text="e.g., UQ-2025-0001"
    )
    financial_year = models.CharField(
        max_length=9,
        choices=FINANCIAL_YEAR_CHOICES
    )
    created_at = models.DateTimeField(auto_now_add=True)
    demand_notes = models.ManyToManyField(
        DemandNote,
        related_name='ultimate_queries',
        help_text="Demand notes consolidated into this query"
    )
    is_purchased = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Ultimate Query'
        verbose_name_plural = 'Ultimate Queries'

    def __str__(self):
        return f"{self.query_no} ({self.financial_year})"


class UltimateQueryItem(models.Model):
    """
    Individual summarized items within an UltimateQuery.
    """
    ultimate_query = models.ForeignKey(
        UltimateQuery,
        on_delete=models.CASCADE,
        related_name='items'
    )
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    total_quantity = models.PositiveIntegerField()
    estimated_rate = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text="Rate at time of query generation"
    )

    class Meta:
        verbose_name = 'Ultimate Query Item'
        verbose_name_plural = 'Ultimate Query Items'
        unique_together = ['ultimate_query', 'item']

    @property
    def total_estimated_cost(self):
        return self.total_quantity * self.estimated_rate

    def __str__(self):
        return f"{self.item.item_name} x {self.total_quantity} for {self.ultimate_query.query_no}"
