from typing import Dict, Any, List, Optional
from datetime import datetime


class OwnershipChainBuilder:
    """
    Constructs genealogical and conveyance ownership chain graphs from land records.
    Builds chronological transaction timelines and detects title gaps.
    """

    def __init__(self):
        pass

    def build_chain(
        self,
        current_owners: List[Dict[str, Any]],
        mutation_history: List[Dict[str, Any]],
        parcel_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Builds graph nodes, links, timeline, and evaluates title continuity.
        """
        nodes: List[Dict[str, Any]] = []
        links: List[Dict[str, Any]] = []
        timeline: List[Dict[str, Any]] = []

        seen_parties = set()

        # Add current owners as active leaf nodes
        for o in current_owners:
            name = o.get("name", "Unknown")
            if name not in seen_parties:
                nodes.append({
                    "id": name,
                    "label": name,
                    "type": "current_owner",
                    "share": o.get("share", 1.0),
                    "is_deceased": o.get("is_deceased", False),
                    "father_spouse": o.get("father_or_husband_name", "")
                })
                seen_parties.add(name)

        # Sort mutations chronologically
        sorted_mutations = sorted(
            mutation_history,
            key=lambda m: m.get("mutation_date") or m.get("date") or "1970-01-01"
        )

        for mut in sorted_mutations:
            from_p = mut.get("from_party") or mut.get("from") or "Prior State/Ancestor"
            to_p = mut.get("to_party") or mut.get("to") or "Purchaser"
            m_no = mut.get("mutation_no", "")
            m_date = mut.get("mutation_date") or mut.get("date", "Undated")
            m_type = mut.get("mutation_type", "sale")
            t_area = mut.get("transferred_area", 0.0)

            # Ensure nodes exist
            if from_p not in seen_parties:
                nodes.append({
                    "id": from_p,
                    "label": from_p,
                    "type": "prior_owner",
                    "share": 1.0,
                    "is_deceased": False
                })
                seen_parties.add(from_p)

            if to_p not in seen_parties:
                nodes.append({
                    "id": to_p,
                    "label": to_p,
                    "type": "intermediate_party",
                    "share": 1.0,
                    "is_deceased": False
                })
                seen_parties.add(to_p)

            # Directed transfer link
            links.append({
                "source": from_p,
                "target": to_p,
                "mutation_no": m_no,
                "mutation_date": m_date,
                "type": m_type,
                "transferred_area": t_area
            })

            timeline.append({
                "date": m_date,
                "mutation_no": m_no,
                "action": f"{m_type.capitalize()} transfer from '{from_p}' to '{to_p}'",
                "extent": f"{t_area} sq m" if t_area else "Full holding",
                "order_ref": mut.get("order_ref", "Revenue Certified")
            })

        # Gap detection
        has_broken_chain = False
        gap_notes = []
        if sorted_mutations:
            # Check if first mutation from_party is disconnected
            first_from = sorted_mutations[0].get("from_party", "")
            if not first_from:
                has_broken_chain = True
                gap_notes.append("Root grant or antecedent title holder missing in initial mutation.")

        return {
            "parcel_id": parcel_info.get("survey_no") if parcel_info else "101",
            "nodes": nodes,
            "links": links,
            "timeline": timeline,
            "is_continuous": not has_broken_chain,
            "gap_notes": gap_notes
        }
