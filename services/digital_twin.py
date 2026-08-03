class SupplyChainDigitalTwin:
    def __init__(self):
        # Nodes represent facilities, suppliers, warehouses, transport networks
        self.nodes = [
            {"id": "plant_mumbai", "label": "Mumbai Plant (IN)", "type": "Facility", "emission_rate": "High"},
            {"id": "supplier_steelcorp", "label": "SteelCorp (IN)", "type": "Supplier", "emission_rate": "Medium"},
            {"id": "route_freight", "label": "HGV Road Freight", "type": "Transport Route", "emission_rate": "Medium"},
            {"id": "warehouse_hamburg", "label": "Hamburg Warehouse (DE)", "type": "Warehouse", "emission_rate": "Low"},
            {"id": "plant_munich", "label": "Munich Processing (DE)", "type": "Facility", "emission_rate": "Low"}
        ]
        # Links represent material flow, energy grid mapping, transport corridors
        self.links = [
            {"source": "supplier_steelcorp", "target": "plant_mumbai", "type": "Material Flow", "carbon_flow_kg": 2861.0},
            {"source": "plant_mumbai", "target": "route_freight", "type": "Transport Corridor", "carbon_flow_kg": 1500.0},
            {"source": "route_freight", "target": "warehouse_hamburg", "type": "Logistics Route", "carbon_flow_kg": 850.0},
            {"source": "warehouse_hamburg", "target": "plant_munich", "type": "Inter-Plant Transfer", "carbon_flow_kg": 250.0}
        ]

    def get_digital_twin_model(self):
        return {
            "organization": "EcoSteel Europe",
            "nodes": self.nodes,
            "links": self.links,
            "hotspots": [
                {"node_id": "plant_mumbai", "score": 85.0, "reason": "Fossil-heavy national electricity grid mapping"},
                {"node_id": "supplier_steelcorp", "score": 68.0, "reason": "Coal combustion in blast furnaces"}
            ]
        }

if __name__ == "__main__":
    twin = SupplyChainDigitalTwin()
    graph = twin.get_digital_twin_model()
    import json
    print(json.dumps(graph, indent=2))
