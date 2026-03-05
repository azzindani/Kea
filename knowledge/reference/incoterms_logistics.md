---
name: "Incoterms (International Commercial Terms)"
description: "A series of pre-defined commercial terms published by the International Chamber of Commerce (ICC) relating to international commercial law."
domain: "logistics"
tags: ["reference", "logistics", "law", "trade", "incoterms"]
---

# Standards & Authorities
*   **Publisher**: International Chamber of Commerce (ICC).
*   **Latest Version**: Incoterms 2020.
*   **Focus**: Allocation of costs, risks, and responsibilities between buyers and sellers in the global transport and delivery of goods.

## Core Framework
1.  **EXW (Ex Works)**: The seller makes the goods available at their premises. The buyer bears all risk and cost from that point forward.
2.  **FOB (Free on Board)**: The seller delivers the goods on board the vessel nominated by the buyer. Risk passes when the goods are on board.
3.  **CIF (Cost, Insurance and Freight)**: The seller pays for the carriage and insurance to the named port of destination. Risk passes to the buyer when the goods are on board the ship.
4.  **DDP (Delivered Duty Paid)**: The seller bears all risks and costs, including import duties and taxes, to the named place of destination.

## Application in Kea (Digital Logic)
*   **Data Delivery Contracts**: Use the Incoterm "Metaphor" for data transfer:
    *   **EXW-Data**: "The raw data is in the DB; you fetch it and process it (Your risk/cost)."
    *   **DDP-Data**: "I will process the data, clean it, and deliver it directly to your endpoint (My risk/cost)."
*   **Service Level Agreements (SLAs)**: Clearly define the "Transfer of Risk" point in a multi-service DAG. If Service A fails *after* successful delivery to Service B, who owns the "Clean-up"?
*   **Supply Chain Audits**: When evaluating a hardware or cloud provider, verify their exact Incoterm responsibility to ensure no "Hidden Costs" (e.g., Egress fees or local taxes).
破位
