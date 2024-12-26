package homeassistant

default allow = false

allow {
    parts := split(input.entity_id, ".")
    domain := parts[0]
    has_permission(input.user, domain, input.action)
}

has_permission(user, domain, action) {
    user.role == "admin"
}

has_permission(user, domain, action) {
    user.role == "user"
    domain in ["light", "switch"]
    action in ["turn_on", "turn_off"]
}

has_permission(user, domain, action) {
    user.role == "restricted"
    action == "get_state"
}

allow {
    current_hour := time.clock(input.timestamp)[0]
    current_hour >= 6
    current_hour < 23
    has_permission(input.user, domain, input.action)
}