#!/bin/bash
# Script pour configurer la planification automatique quotidienne sur macOS (launchd)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLIST_NAME="com.bafang.youtube.upload"
PLIST_FILE="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"
PYTHON_PATH=$(which python3)

echo "🔧 Configuration de la planification automatique YouTube Upload"
echo ""

# Créer le fichier plist pour launchd
cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_NAME}</string>
    <key>ProgramArguments</key>
    <array>
        <string>${PYTHON_PATH}</string>
        <string>${SCRIPT_DIR}/auto_upload_multilingual.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>${SCRIPT_DIR}</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>${SCRIPT_DIR}/upload_log.txt</string>
    <key>StandardErrorPath</key>
    <string>${SCRIPT_DIR}/upload_error_log.txt</string>
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
EOF

echo "✅ Fichier plist créé: $PLIST_FILE"
echo ""

# Charger le service
launchctl unload "$PLIST_FILE" 2>/dev/null
launchctl load "$PLIST_FILE"

echo "✅ Service chargé dans launchd"
echo ""
echo "📅 Le script sera exécuté automatiquement chaque jour à 9h00"
echo ""
echo "Commandes utiles:"
echo "  - Voir les logs: tail -f ${SCRIPT_DIR}/upload_log.txt"
echo "  - Arrêter: launchctl unload $PLIST_FILE"
echo "  - Redémarrer: launchctl unload $PLIST_FILE && launchctl load $PLIST_FILE"
echo "  - Vérifier le statut: launchctl list | grep ${PLIST_NAME}"
echo ""

