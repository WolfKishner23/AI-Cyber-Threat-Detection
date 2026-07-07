import os

# 1. Update App.jsx
app_path = "frontend/src/App.jsx"
with open(app_path, "r") as f:
    app_content = f.read()

customer_map_code = """
  // Extract customer map from events
  const customerMap = useMemo(() => {
    const map = {};
    events.forEach(evt => {
      const profile = evt.raw_payload?.simulation?.customer_profile;
      if (profile && profile.customer_id) {
        map[profile.customer_id] = profile.full_name;
      }
    });
    return map;
  }, [events]);
"""
if "const customerMap =" not in app_content:
    app_content = app_content.replace(
        "const filteredAlerts = useMemo(() => {",
        customer_map_code + "\n  const filteredAlerts = useMemo(() => {"
    )

app_content = app_content.replace(
    """<td style={{ fontFamily: 'monospace' }}>{evt.user_id}</td>""",
    """<td>
                              <div style={{ fontWeight: 500 }}>{customerMap[evt.user_id] || evt.user_id}</div>
                              {customerMap[evt.user_id] && <div style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: 'var(--text-secondary)' }}>{evt.user_id}</div>}
                            </td>"""
)

app_content = app_content.replace(
    "alert={alert}",
    "alert={alert}\n                      customerMap={customerMap}"
)

app_content = app_content.replace(
    "investigations={filteredInvestigations}",
    "investigations={filteredInvestigations}\n                  customerMap={customerMap}"
)

app_content = app_content.replace(
    "inv={selectedInvestigation}",
    "inv={selectedInvestigation}\n            customerMap={customerMap}"
)

with open(app_path, "w") as f:
    f.write(app_content)

# 2. Update AlertCard.jsx
alert_path = "frontend/src/components/AlertCard.jsx"
with open(alert_path, "r") as f:
    alert_content = f.read()

alert_content = alert_content.replace(
    "const AlertCard = ({ alert, onRunInvestigation, isRunning }) => {",
    "const AlertCard = ({ alert, onRunInvestigation, isRunning, customerMap }) => {\n  const customerName = customerMap?.[alert.event?.user_id] || alert.event?.user_id;"
)

alert_content = alert_content.replace(
    """<div className="alert-meta">""",
    """<div className="alert-meta" style={{ marginBottom: '0.5rem' }}>
        <div style={{ fontWeight: 500 }}>{customerName} {customerMap?.[alert.event?.user_id] && <span style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: 'var(--text-secondary)', marginLeft: '4px' }}>{alert.event?.user_id}</span>}</div>
      </div>
      <div className="alert-meta">"""
)
with open(alert_path, "w") as f:
    f.write(alert_content)

# 3. Update InvestigationTable.jsx
table_path = "frontend/src/components/InvestigationTable.jsx"
with open(table_path, "r") as f:
    table_content = f.read()

table_content = table_content.replace(
    "const InvestigationTable = ({ investigations, onSelect }) => {",
    "const InvestigationTable = ({ investigations, onSelect, customerMap }) => {"
)
table_content = table_content.replace(
    """<td style={{ fontFamily: 'monospace' }}>{inv.customer_id}</td>""",
    """<td>
                  <div style={{ fontWeight: 500 }}>{customerMap?.[inv.customer_id] || inv.customer_id}</div>
                  {customerMap?.[inv.customer_id] && <div style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: 'var(--text-secondary)' }}>{inv.customer_id}</div>}
              </td>"""
)
with open(table_path, "w") as f:
    f.write(table_content)

# 4. Update InvestigationModal.jsx
modal_path = "frontend/src/components/InvestigationModal.jsx"
with open(modal_path, "r") as f:
    modal_content = f.read()

modal_content = modal_content.replace(
    "const InvestigationModal = ({ inv, onClose }) => {",
    "const InvestigationModal = ({ inv, onClose, customerMap }) => {\n  const customerName = customerMap?.[inv.customer_id] || inv.customer_id;"
)
modal_content = modal_content.replace(
    "Customer ID: {inv.customer_id} • Alert ID: #{inv.alert_id}",
    "{customerName} {customerMap?.[inv.customer_id] ? `(${inv.customer_id})` : ''} • Alert ID: #{inv.alert_id}"
)
with open(modal_path, "w") as f:
    f.write(modal_content)

print("Updated frontend components successfully.")
