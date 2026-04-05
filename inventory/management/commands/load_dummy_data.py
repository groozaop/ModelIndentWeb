"""
Load dummy trades, item groups, and items for testing.
Usage: python manage.py load_dummy_data
"""

from django.core.management.base import BaseCommand
from inventory.models import Trade, ItemGroup, Item


class Command(BaseCommand):
    help = 'Loads dummy trades, item groups, and items into the database'

    def handle(self, *args, **options):

        # ── Trades ────────────────────────────────────────
        trades_data = [
            ('COPA (Computer Operator & Programming Assistant)', 4),
            ('Wireman', 4),
            ('Fitter', 4),
            ('Electrician', 4),
            ('Turner', 4),
            ('Welder', 4),
            ('Mechanic Motor Vehicle (MMV)', 4),
            ('Plumber', 4),
            ('Carpenter', 4),
            ('Electronics Mechanic', 4),
        ]

        for name, semesters in trades_data:
            obj, created = Trade.objects.get_or_create(
                trade_name=name,
                defaults={'total_semesters': semesters}
            )
            status = 'Created' if created else 'Exists'
            self.stdout.write(f'  [{status}] Trade: {name}')

        # ── Item Groups ───────────────────────────────────
        groups_data = [
            ('Computer & IT Consumables', 'Keyboards, mice, cables, USB drives, ink cartridges, etc.'),
            ('Electrical Materials', 'Wires, switches, fuses, MCBs, conduits, tapes, etc.'),
            ('Hand Tools', 'Hammers, pliers, screwdrivers, spanners, files, etc.'),
            ('Measuring Instruments', 'Vernier calipers, micrometers, multimeters, gauges, etc.'),
            ('Raw Materials', 'Mild steel, copper, aluminum, PVC pipes, wood, etc.'),
            ('Safety Equipment', 'Gloves, goggles, helmets, aprons, fire extinguishers, etc.'),
            ('Welding Consumables', 'Electrodes, gas cylinders, nozzles, welding rods, etc.'),
            ('Stationery & Office', 'Registers, papers, markers, chalk, dusters, etc.'),
            ('Plumbing Materials', 'GI pipes, fittings, valves, taps, teflon tape, etc.'),
            ('Electronic Components', 'Resistors, capacitors, ICs, PCBs, LEDs, soldering wire, etc.'),
        ]

        groups = {}
        for name, desc in groups_data:
            obj, created = ItemGroup.objects.get_or_create(
                name=name,
                defaults={'description': desc}
            )
            groups[name] = obj
            status = 'Created' if created else 'Exists'
            self.stdout.write(f'  [{status}] Group: {name}')

        # ── Items ─────────────────────────────────────────
        items_data = [
            # Computer & IT Consumables
            ('IT-001', 'USB Keyboard', 'Nos', 350, 'Computer & IT Consumables'),
            ('IT-002', 'USB Optical Mouse', 'Nos', 250, 'Computer & IT Consumables'),
            ('IT-003', 'USB Pen Drive 32GB', 'Nos', 300, 'Computer & IT Consumables'),
            ('IT-004', 'HDMI Cable 1.5m', 'Nos', 200, 'Computer & IT Consumables'),
            ('IT-005', 'LAN Cable Cat6 (per mtr)', 'Mtr', 15, 'Computer & IT Consumables'),
            ('IT-006', 'Inkjet Printer Cartridge (Black)', 'Nos', 850, 'Computer & IT Consumables'),
            ('IT-007', 'RJ45 Connector', 'Nos', 8, 'Computer & IT Consumables'),
            ('IT-008', 'Thermal Paste Tube', 'Nos', 150, 'Computer & IT Consumables'),

            # Electrical Materials
            ('EL-001', 'Copper Wire 1.5 sq mm (per mtr)', 'Mtr', 18, 'Electrical Materials'),
            ('EL-002', 'Copper Wire 2.5 sq mm (per mtr)', 'Mtr', 28, 'Electrical Materials'),
            ('EL-003', 'PVC Insulation Tape', 'Nos', 25, 'Electrical Materials'),
            ('EL-004', 'MCB 16A Single Pole', 'Nos', 180, 'Electrical Materials'),
            ('EL-005', 'Switch Board 6x6', 'Nos', 120, 'Electrical Materials'),
            ('EL-006', 'Modular Switch 6A', 'Nos', 45, 'Electrical Materials'),
            ('EL-007', 'Ceiling Rose', 'Nos', 15, 'Electrical Materials'),
            ('EL-008', 'LED Bulb 9W', 'Nos', 85, 'Electrical Materials'),

            # Hand Tools
            ('HT-001', 'Ball Peen Hammer 500g', 'Nos', 320, 'Hand Tools'),
            ('HT-002', 'Combination Plier 8"', 'Nos', 280, 'Hand Tools'),
            ('HT-003', 'Flat Screwdriver 6"', 'Nos', 90, 'Hand Tools'),
            ('HT-004', 'Phillips Screwdriver 6"', 'Nos', 95, 'Hand Tools'),
            ('HT-005', 'Hacksaw Frame with Blade', 'Nos', 220, 'Hand Tools'),
            ('HT-006', 'Flat File 10"', 'Nos', 150, 'Hand Tools'),
            ('HT-007', 'Ring Spanner Set (6-32mm)', 'Set', 950, 'Hand Tools'),
            ('HT-008', 'Wire Stripper', 'Nos', 180, 'Hand Tools'),

            # Measuring Instruments
            ('MI-001', 'Vernier Caliper 150mm', 'Nos', 1200, 'Measuring Instruments'),
            ('MI-002', 'Outside Micrometer 0-25mm', 'Nos', 1500, 'Measuring Instruments'),
            ('MI-003', 'Digital Multimeter', 'Nos', 650, 'Measuring Instruments'),
            ('MI-004', 'Steel Rule 300mm', 'Nos', 80, 'Measuring Instruments'),
            ('MI-005', 'Try Square 6"', 'Nos', 350, 'Measuring Instruments'),

            # Raw Materials
            ('RM-001', 'MS Flat Bar 25x6mm (per kg)', 'Kg', 65, 'Raw Materials'),
            ('RM-002', 'MS Round Bar 12mm dia (per kg)', 'Kg', 60, 'Raw Materials'),
            ('RM-003', 'Copper Sheet 20 SWG (per kg)', 'Kg', 750, 'Raw Materials'),
            ('RM-004', 'Aluminium Sheet 18 SWG (per kg)', 'Kg', 280, 'Raw Materials'),
            ('RM-005', 'PVC Pipe 1" (per mtr)', 'Mtr', 55, 'Raw Materials'),
            ('RM-006', 'Softwood Plank 2x4" (per cft)', 'Cft', 900, 'Raw Materials'),

            # Safety Equipment
            ('SE-001', 'Leather Hand Gloves (pair)', 'Pair', 120, 'Safety Equipment'),
            ('SE-002', 'Safety Goggles', 'Nos', 150, 'Safety Equipment'),
            ('SE-003', 'Safety Helmet', 'Nos', 250, 'Safety Equipment'),
            ('SE-004', 'Leather Apron', 'Nos', 350, 'Safety Equipment'),
            ('SE-005', 'Ear Plug (pair)', 'Pair', 30, 'Safety Equipment'),

            # Welding Consumables
            ('WC-001', 'Welding Electrode 3.15mm (per kg)', 'Kg', 120, 'Welding Consumables'),
            ('WC-002', 'Welding Electrode 2.5mm (per kg)', 'Kg', 130, 'Welding Consumables'),
            ('WC-003', 'Welding Nozzle No. 2', 'Nos', 75, 'Welding Consumables'),
            ('WC-004', 'Chipping Hammer', 'Nos', 180, 'Welding Consumables'),

            # Stationery & Office
            ('ST-001', 'A4 Paper Ream (500 sheets)', 'Ream', 280, 'Stationery & Office'),
            ('ST-002', 'Whiteboard Marker (set of 4)', 'Set', 120, 'Stationery & Office'),
            ('ST-003', 'Attendance Register', 'Nos', 60, 'Stationery & Office'),
            ('ST-004', 'Chalk Box (white)', 'Box', 35, 'Stationery & Office'),
            ('ST-005', 'Duster Cloth', 'Nos', 20, 'Stationery & Office'),

            # Plumbing Materials
            ('PL-001', 'GI Pipe 1/2" (per mtr)', 'Mtr', 180, 'Plumbing Materials'),
            ('PL-002', 'GI Elbow 1/2"', 'Nos', 25, 'Plumbing Materials'),
            ('PL-003', 'Gate Valve 1/2"', 'Nos', 280, 'Plumbing Materials'),
            ('PL-004', 'Teflon Tape Roll', 'Nos', 20, 'Plumbing Materials'),
            ('PL-005', 'Bib Cock 1/2"', 'Nos', 180, 'Plumbing Materials'),

            # Electronic Components
            ('EC-001', 'Resistor Assorted Kit (600pcs)', 'Kit', 250, 'Electronic Components'),
            ('EC-002', 'Capacitor Assorted Kit (300pcs)', 'Kit', 350, 'Electronic Components'),
            ('EC-003', 'Breadboard 830 points', 'Nos', 120, 'Electronic Components'),
            ('EC-004', 'Soldering Iron 25W', 'Nos', 180, 'Electronic Components'),
            ('EC-005', 'Soldering Wire 60/40 (per mtr)', 'Mtr', 15, 'Electronic Components'),
            ('EC-006', 'LED 5mm Assorted (pack of 100)', 'Pack', 80, 'Electronic Components'),
        ]

        created_count = 0
        for code, name, unit, price, group_name in items_data:
            obj, created = Item.objects.get_or_create(
                item_code=code,
                defaults={
                    'item_name': name,
                    'item_unit': unit,
                    'est_price': price,
                    'group': groups[group_name],
                }
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Done! Created {created_count} new items '
            f'(Total: {Item.objects.count()} items in {ItemGroup.objects.count()} groups, '
            f'{Trade.objects.count()} trades)'
        ))
