import os
import django
import random
from datetime import datetime, timedelta

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_project.settings')
django.setup()

from django.contrib.auth.models import User, Group
from inventory.models import (
    ItemGroup, Item, Trade, Instructor, DemandNote, DemandItem,
    FINANCIAL_YEAR_CHOICES
)

def seed():
    # 1. Create Groups
    storekeepers_group, _ = Group.objects.get_or_create(name='StoreKeepers')
    instructors_group, _ = Group.objects.get_or_create(name='Instructors')

    # 2. Create Trade & Group dummy data
    trades_data = [
        ('Electrician', 4),
        ('Fitter', 4),
        ('Wireman', 4),
        ('Welder', 2),
        ('COPA', 2),
        ('ICTSM', 4),
    ]
    for name, sems in trades_data:
        Trade.objects.get_or_create(trade_name=name, defaults={'total_semesters': sems})

    groups_data = ['Tools & Equipment', 'Stationery & Office', 'Raw Materials', 'Computer & IT Consumables']
    for gname in groups_data:
        ItemGroup.objects.get_or_create(name=gname)

    # 3. Create Items
    items_data = [
        ('T-001', 'Hammer 500g', 'Tools & Equipment', 'Nos', 350.00),
        ('T-002', 'Plier 8 inch', 'Tools & Equipment', 'Nos', 280.00),
        ('S-001', 'White Paper A4', 'Stationery & Office', 'Ream', 290.00),
        ('S-002', 'Pen Blue (Pack of 10)', 'Stationery & Office', 'Pack', 100.00),
        ('M-001', 'Mild Steel Plate', 'Raw Materials', 'Kg', 85.00),
        ('M-002', 'Copper Wire 1.5 sqmm', 'Raw Materials', 'Meter', 45.00),
        ('I-001', 'Cat6 Network Cable', 'Computer & IT Consumables', 'Meter', 25.00),
        ('I-002', 'RJ45 Connectors (Box of 100)', 'Computer & IT Consumables', 'Box', 850.00),
    ]

    items_objs = []
    for code, name, gname, unit, price in items_data:
        group = ItemGroup.objects.get(name=gname)
        item, _ = Item.objects.get_or_create(
            item_code=code,
            defaults={'item_name': name, 'item_unit': unit, 'est_price': price, 'group': group}
        )
        items_objs.append(item)

    # 4. Create Dummy Instructors
    instructors_names = [
        ('vinod_elec', 'Vinod Sawant', 'Electrician'),
        ('amit_fitter', 'Amit Sharma', 'Fitter'),
        ('sunita_ictsm', 'Sunita Patil', 'ICTSM'),
    ]

    for username, full_name, trade_name in instructors_names:
        user, created = User.objects.get_or_create(username=username)
        if created:
            user.set_password('Test@1234')
            user.save()
        user.groups.add(instructors_group)

        trade = Trade.objects.get(trade_name=trade_name)
        Instructor.objects.get_or_create(user=user, defaults={'name': full_name, 'trade': trade})

    # 5. Create Dummy Demands
    instructor_objs = Instructor.objects.all()
    statuses = ['SUBMITTED', 'MERGED', 'DRAFT']
    fy_list = [f[0] for f in FINANCIAL_YEAR_CHOICES]

    for instructor in instructor_objs:
        for status in statuses:
            # Create a demand note
            dn = DemandNote.objects.create(
                instructor=instructor,
                trade=instructor.trade,
                semester_no=random.choice([1, 2, 3, 4]),
                financial_year=random.choice(fy_list),
                status=status,
                remarks=f"Sample {status} demand note for {instructor.trade.trade_name}",
                created_at=datetime.now() - timedelta(days=random.randint(1, 30))
            )
            
            if status != 'DRAFT':
                dn.submitted_at = dn.created_at + timedelta(hours=2)
                dn.save()

            # Add 2-4 items to each note
            selected_items = random.sample(items_objs, k=random.randint(2, 4))
            for item in selected_items:
                DemandItem.objects.create(
                    demand_note=dn,
                    item=item,
                    quantity_required=random.randint(5, 50)
                )

    print(f"Seeding completed successfully! Created {instructor_objs.count()} instructors and {DemandNote.objects.count()} demand notes.")

if __name__ == '__main__':
    seed()
