#!/usr/bin/with-contenv bashio
bashio::log.info "Starting OPA Authorization add-on..."

# Install OPA if not already installed
if ! command -v opa >/dev/null 2>&1; then
    bashio::log.info "Installing OPA..."
    curl -L -o /usr/local/bin/opa https://openpolicyagent.org/downloads/v0.42.0/opa_linux_amd64
    chmod +x /usr/local/bin/opa
fi

# Install Python dependencies
bashio::log.info "Installing Python dependencies..."
pip3 install aiohttp requests voluptuous

# Start s6-overlay
exec /init