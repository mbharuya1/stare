#!/usr/bin/env bash
# Stare EC2 bootstrap. Run this ONCE per fresh Ubuntu 22.04 instance.
# Re-running is safe: every step is idempotent.
#
#   curl -fsSL https://raw.githubusercontent.com/mbharuya1/stare/main/scripts/deploy_ec2.sh | bash
# or, after SSHing into the box:
#   bash scripts/deploy_ec2.sh
#
# What it does, in order:
#   1. apt update + install Docker Engine + the compose plugin
#   2. Add the current user to the 'docker' group (so sudo is not needed)
#   3. Clone (or pull) the Stare repo into ~/stare
#   4. Print the next manual steps: scp data/, fill in docker/.env, compose up

set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/mbharuya1/stare.git}"
REPO_DIR="${REPO_DIR:-$HOME/stare}"
LOG_PREFIX="[deploy_ec2]"

log() { echo "$LOG_PREFIX $*"; }

# ───────────────────────── 1. apt + Docker ─────────────────────────
install_docker() {
    if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
        log "Docker + compose plugin already installed: $(docker --version)"
        return 0
    fi

    log "Installing Docker Engine + compose plugin"
    sudo apt-get update -y
    sudo apt-get install -y \
        ca-certificates curl gnupg lsb-release rsync

    # Docker official apt repo
    sudo install -m 0755 -d /etc/apt/keyrings
    if [ ! -f /etc/apt/keyrings/docker.gpg ]; then
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
            | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
        sudo chmod a+r /etc/apt/keyrings/docker.gpg
    fi

    UBUNTU_CODENAME="$(. /etc/os-release && echo "$VERSION_CODENAME")"
    echo \
"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu $UBUNTU_CODENAME stable" \
        | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    sudo apt-get update -y
    sudo apt-get install -y \
        docker-ce docker-ce-cli containerd.io \
        docker-buildx-plugin docker-compose-plugin

    sudo systemctl enable --now docker
    log "Docker installed: $(docker --version)"
}

# ───────────────────────── 2. docker group ─────────────────────────
add_user_to_docker_group() {
    local user="${SUDO_USER:-$USER}"
    if id -nG "$user" | tr ' ' '\n' | grep -qx docker; then
        log "$user is already in the docker group"
        return 0
    fi
    log "Adding $user to the docker group (re-login required to take effect)"
    sudo usermod -aG docker "$user"
}

# ───────────────────────── 3. clone repo ───────────────────────────
clone_or_update_repo() {
    if [ -d "$REPO_DIR/.git" ]; then
        log "Repo already at $REPO_DIR, pulling latest"
        git -C "$REPO_DIR" fetch --quiet origin
        git -C "$REPO_DIR" pull --ff-only
    else
        log "Cloning $REPO_URL into $REPO_DIR"
        git clone --depth 1 "$REPO_URL" "$REPO_DIR"
    fi

    # Make sure docker/.env exists (copy from example if missing).
    if [ ! -f "$REPO_DIR/docker/.env" ]; then
        cp "$REPO_DIR/docker/.env.example" "$REPO_DIR/docker/.env"
        log "Created docker/.env from example. FILL IN secrets before docker compose up"
    fi
}

# ───────────────────────── 4. next steps ───────────────────────────
print_next_steps() {
    cat <<EOF

──────────────────────────────────────────────────────────────────────
$LOG_PREFIX bootstrap complete. Next steps (run from your laptop):

1. Upload the corpus + index (about 2 GB total) over rsync:

       rsync -avzP --partial \\
             ./data/raw/ ./data/processed/ ./data/cached/ \\
             ubuntu@$(curl -s ifconfig.me):$REPO_DIR/data/

   The data/ tree is gitignored, so the clone above shipped only the
   .gitkeep placeholders.

2. SSH back in and edit secrets:

       ssh ubuntu@$(curl -s ifconfig.me)
       nano $REPO_DIR/docker/.env
       # Fill in DOMAIN, ACME_EMAIL, ANTHROPIC_API_KEY, etc.

3. Bring the stack up:

       cd $REPO_DIR
       docker compose -f docker/docker-compose.yml --env-file docker/.env up -d

4. Verify (replace <domain> with what you set in docker/.env):

       curl https://<domain>/api/health
       open https://<domain>/

If you have not pointed DNS yet, the same URLs work over plain HTTP on
the instance's public IP. Caddy will switch to HTTPS automatically the
first time the configured DOMAIN resolves to this box.
──────────────────────────────────────────────────────────────────────
EOF
}

main() {
    install_docker
    add_user_to_docker_group
    clone_or_update_repo
    print_next_steps
}

main "$@"
