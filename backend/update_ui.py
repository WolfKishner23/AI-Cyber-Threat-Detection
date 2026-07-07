import os

def update_app_jsx():
    path = "frontend/src/App.jsx"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update customerMap to store the whole profile instead of just name
    content = content.replace(
        "map[profile.customer_id] = profile.full_name;",
        "map[profile.customer_id] = profile;"
    )

    # 2. Add maskAccount helper if not present
    mask_helper = """
  const maskAccount = (accountNum) => {
    if (!accountNum) return '';
    const str = String(accountNum);
    if (str.length <= 4) return str;
    return `**** **** ${str.slice(-4)}`;
  };
"""
    if "const maskAccount" not in content:
        content = content.replace(
            "const showToast = (message, type = 'success') => {",
            mask_helper + "\n  const showToast = (message, type = 'success') => {"
        )

    # 3. Pass maskAccount to child components
    content = content.replace(
        "customerMap={customerMap}",
        "customerMap={customerMap}\n                      maskAccount={maskAccount}"
    )
    content = content.replace(
        "investigations={filteredInvestigations}\n                  customerMap={customerMap}",
        "investigations={filteredInvestigations}\n                  customerMap={customerMap}\n                  maskAccount={maskAccount}"
    )
    content = content.replace(
        "inv={selectedInvestigation}\n            customerMap={customerMap}",
        "inv={selectedInvestigation}\n            customerMap={customerMap}\n            maskAccount={maskAccount}"
    )

    # 4. Update the dashboard table render
    content = content.replace(
        """<div style={{ fontWeight: 500 }}>{customerMap[evt.user_id] || evt.user_id}</div>
                              {customerMap[evt.user_id] && <div style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: 'var(--text-secondary)' }}>{evt.user_id}</div>}""",
        """<div style={{ fontWeight: 500 }}>👤 {customerMap[evt.user_id]?.full_name || evt.user_id}</div>
                              <div style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: 'var(--text-secondary)' }}>Customer ID: {evt.user_id}</div>
                              {customerMap[evt.user_id]?.account_number && <div style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: 'var(--text-secondary)' }}>Account: {maskAccount(customerMap[evt.user_id].account_number)}</div>}"""
    )
    
    # 5. Update filtering logic for matchesSearch (if it uses customerMap[i.customer_id].toLowerCase())
    content = content.replace(
        "customerMap[i.customer_id].toLowerCase().includes",
        "customerMap[i.customer_id]?.full_name?.toLowerCase().includes"
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def update_alert_card():
    path = "frontend/src/components/AlertCard.jsx"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    content = content.replace(
        "const AlertCard = ({ alert, onRunInvestigation, isRunning, customerMap }) => {",
        "const AlertCard = ({ alert, onRunInvestigation, isRunning, customerMap, maskAccount }) => {"
    )
    content = content.replace(
        "const profile = customerMap?.[alert.event?.user_id];\n  const customerName = profile?.full_name || alert.event?.user_id;",
        "const profile = customerMap?.[alert.event?.user_id];\n  const customerName = profile?.full_name || alert.event?.user_id;"
    )

    content = content.replace(
        """<div style={{ fontWeight: 500 }}>{customerName} {customerMap?.[alert.event?.user_id] && <span style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: 'var(--text-secondary)', marginLeft: '4px' }}>{alert.event?.user_id}</span>}</div>""",
        """<div style={{ fontWeight: 500 }}>👤 {customerName}</div>
        <div style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: 'var(--text-secondary)' }}>Customer ID: {alert.event?.user_id}</div>
        {profile?.account_number && <div style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: 'var(--text-secondary)' }}>Account: {maskAccount(profile.account_number)}</div>}"""
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def update_investigation_table():
    path = "frontend/src/components/InvestigationTable.jsx"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    content = content.replace(
        "const InvestigationTable = ({ investigations, onSelect, customerMap }) => {",
        "const InvestigationTable = ({ investigations, onSelect, customerMap, maskAccount }) => {"
    )
    content = content.replace(
        """<div style={{ fontWeight: 500 }}>{customerMap?.[inv.customer_id] || inv.customer_id}</div>
                  {customerMap?.[inv.customer_id] && <div style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: 'var(--text-secondary)' }}>{inv.customer_id}</div>}""",
        """<div style={{ fontWeight: 500 }}>👤 {customerMap?.[inv.customer_id]?.full_name || inv.customer_id}</div>
                  <div style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: 'var(--text-secondary)' }}>Customer ID: {inv.customer_id}</div>
                  {customerMap?.[inv.customer_id]?.account_number && <div style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: 'var(--text-secondary)' }}>Account: {maskAccount(customerMap[inv.customer_id].account_number)}</div>}"""
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def update_investigation_modal():
    path = "frontend/src/components/InvestigationModal.jsx"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    content = content.replace(
        "const InvestigationModal = ({ inv, onClose, customerMap }) => {",
        "const InvestigationModal = ({ inv, onClose, customerMap, maskAccount }) => {"
    )
    content = content.replace(
        "const profile = customerMap?.[inv.customer_id];\n  const customerName = profile?.full_name || inv.customer_id;",
        "const profile = customerMap?.[inv.customer_id];\n  const customerName = profile?.full_name || inv.customer_id;"
    )
    content = content.replace(
        "{customerName} {customerMap?.[inv.customer_id] ? `(${inv.customer_id})` : ''} • Alert ID: #{inv.alert_id}",
        "👤 {customerName} • Customer ID: {inv.customer_id} {profile?.account_number ? `• Account: ${maskAccount(profile.account_number)}` : ''} • Alert ID: #{inv.alert_id}"
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    update_app_jsx()
    update_alert_card()
    update_investigation_table()
    update_investigation_modal()
    print("UI updated successfully.")
