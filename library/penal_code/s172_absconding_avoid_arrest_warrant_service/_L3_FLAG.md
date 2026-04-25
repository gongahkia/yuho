# s172 — L3 flag

- failed: 7, 8
- reason: The encoding makes every case depend on `ordinary_process` or `court_process`, so absconding to avoid arrest on a warrant is not faithfully preserved as a standalone route to the base penalty.
- suggested fix: Model warrant-avoidance separately from summons/notice/order service, and apply the enhanced branch only where the summons, notice or order is for court attendance or production.
