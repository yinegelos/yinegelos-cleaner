"""
YinegelOS Temizleyici v2
Debian tabanlı sistemler için gelişmiş sistem temizleme uygulaması
Düzeltmeler:
  - Race condition: dir_scroll widget geçersizken yazmaya çalışma sorunu giderildi
  - pkexec ile ayrıcalıklı komutlar için GUI şifre istemi
  - Thread'ler arası widget erişimi güvenli hale getirildi
"""

import customtkinter as ctk
import subprocess
import os
import sys
import shutil
import threading
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, filedialog

# ─────────────────────────────────────────────────────────────────────────────
# ÇEVIRI / TRANSLATIONS
# ─────────────────────────────────────────────────────────────────────────────

TRANSLATIONS = {
    "tr": {
        "app_title": "YinegelOS Temizleyici",
        "tab_dashboard": "Pano",
        "tab_apt": "APT Temizliği",
        "tab_flatpak": "Flatpak",
        "tab_userdirs": "Kullanıcı Dizinleri",
        "tab_tips": "Hız Tüyoları",
        "dashboard_welcome": "Sisteminizi Optimize Edin",
        "dashboard_subtitle": "Henüz temizleme yapılmadı",
        "btn_quick_scan": "Hızlı Tarama",
        "btn_clean_all": "Tümünü Temizle",
        "apt_title": "APT Önbellek & Gereksiz Paketler",
        "apt_desc": "Apt önbelleği, gereksiz paketler ve eski çekirdekler temizlenecek.",
        "apt_cache": "APT Önbelleği  (/var/cache/apt)",
        "apt_autoremove": "Gereksiz Paketler  (autoremove)",
        "apt_autoclean": "Eski Önbellekler  (autoclean)",
        "apt_old_kernels": "Eski Linux Çekirdekleri",
        "apt_logs": "Eski Sistem Logları  (/var/log/*.gz)",
        "btn_scan": "Tara",
        "btn_clean": "Seçilileri Temizle",
        "flatpak_title": "Flatpak Yönetimi",
        "flatpak_desc": "Kullanılmayan Flatpak runtime'ları ve önbellekleri temizle.",
        "flatpak_unused": "Kullanılmayan Runtime'lar",
        "flatpak_cache": "Flatpak Önbelleği  (~/.var/app/*/cache)",
        "flatpak_not_found": "Flatpak bu sistemde kurulu değil.",
        "dirs_title": "Kullanıcı Dizinleri Doluluk Oranı",
        "dirs_desc": "Dizinlerin kullandığı alanı görün, seçili dosya/klasörleri silin.",
        "dirs_path": "Yol",
        "dirs_size": "Boyut",
        "dirs_usage": "Doluluk",
        "btn_browse": "Gözat",
        "btn_delete_selected": "Seçilenleri Sil",
        "btn_refresh": "Yenile",
        "tips_title": "Sistem Hız Tüyoları",
        "tips_subtitle": "Sisteminizi hızlandırmak için 10 pratik öneri",
        "lang_label": "Dil",
        "status_idle": "Hazır",
        "status_scanning": "Taranıyor…",
        "status_cleaning": "Temizleniyor…",
        "status_done": "Tamamlandı!",
        "status_error": "Hata oluştu!",
        "confirm_clean": "Seçili öğeler kalıcı olarak silinecek.\nDevam etmek istiyor musunuz?",
        "confirm_title": "Onay",
        "freed_space": "Kazanılan alan",
        "total_found": "Bulunan toplam",
        "no_items": "Temizlenecek bir şey bulunamadı.",
        "scanning_done": "Tarama tamamlandı.",
        "select_all": "Tümünü Seç",
        "deselect_all": "Seçimi Kaldır",
        "disk_usage": "Disk Kullanımı",
        "file_name": "Ad",
        "file_type": "Tür",
        "confirm_delete": "Seçili dosya/klasörler kalıcı olarak silinecek!\nEmin misiniz?",
        "deleted_ok": "Başarıyla silindi.",
        "privilege_error": "Yönetici yetkisi alınamadı. pkexec kurulu mu?",
        "running_as_root": "Uygulama yönetici olarak çalışıyor.",
        "auth_cancelled": "Kimlik doğrulama iptal edildi.",
        "installed_apps": "Kurulu Flatpak Uygulamaları",
        "loading": "Yükleniyor…",
    },
    "en": {
        "app_title": "YinegelOS Cleaner",
        "tab_dashboard": "Dashboard",
        "tab_apt": "APT Cleanup",
        "tab_flatpak": "Flatpak",
        "tab_userdirs": "User Directories",
        "tab_tips": "Speed Tips",
        "dashboard_welcome": "Optimize Your System",
        "dashboard_subtitle": "No cleaning has been performed yet",
        "btn_quick_scan": "Quick Scan",
        "btn_clean_all": "Clean All",
        "apt_title": "APT Cache & Orphan Packages",
        "apt_desc": "Clean apt cache, orphan packages, and old kernels.",
        "apt_cache": "APT Cache  (/var/cache/apt)",
        "apt_autoremove": "Orphan Packages  (autoremove)",
        "apt_autoclean": "Old Caches  (autoclean)",
        "apt_old_kernels": "Old Linux Kernels",
        "apt_logs": "Old System Logs  (/var/log/*.gz)",
        "btn_scan": "Scan",
        "btn_clean": "Clean Selected",
        "flatpak_title": "Flatpak Management",
        "flatpak_desc": "Remove unused Flatpak runtimes and app caches.",
        "flatpak_unused": "Unused Runtimes",
        "flatpak_cache": "Flatpak Cache  (~/.var/app/*/cache)",
        "flatpak_not_found": "Flatpak is not installed on this system.",
        "dirs_title": "User Directory Usage",
        "dirs_desc": "View directory sizes and delete selected files/folders.",
        "dirs_path": "Path",
        "dirs_size": "Size",
        "dirs_usage": "Usage",
        "btn_browse": "Browse",
        "btn_delete_selected": "Delete Selected",
        "btn_refresh": "Refresh",
        "tips_title": "System Speed Tips",
        "tips_subtitle": "10 practical recommendations to speed up your system",
        "lang_label": "Language",
        "status_idle": "Ready",
        "status_scanning": "Scanning…",
        "status_cleaning": "Cleaning…",
        "status_done": "Done!",
        "status_error": "An error occurred!",
        "confirm_clean": "Selected items will be permanently deleted.\nDo you want to continue?",
        "confirm_title": "Confirm",
        "freed_space": "Freed space",
        "total_found": "Total found",
        "no_items": "Nothing to clean.",
        "scanning_done": "Scan completed.",
        "select_all": "Select All",
        "deselect_all": "Deselect All",
        "disk_usage": "Disk Usage",
        "file_name": "Name",
        "file_type": "Type",
        "confirm_delete": "Selected files/folders will be permanently deleted!\nAre you sure?",
        "deleted_ok": "Successfully deleted.",
        "privilege_error": "Could not obtain admin privileges. Is pkexec installed?",
        "running_as_root": "Application is running as administrator.",
        "auth_cancelled": "Authentication was cancelled.",
        "installed_apps": "Installed Flatpak Apps",
        "loading": "Loading…",
    },
    "fr": {
        "app_title": "YinegelOS Nettoyeur",
        "tab_dashboard": "Tableau de bord",
        "tab_apt": "Nettoyage APT",
        "tab_flatpak": "Flatpak",
        "tab_userdirs": "Répertoires",
        "tab_tips": "Conseils",
        "dashboard_welcome": "Optimisez Votre Système",
        "dashboard_subtitle": "Aucun nettoyage effectué",
        "btn_quick_scan": "Analyse rapide",
        "btn_clean_all": "Tout nettoyer",
        "apt_title": "Cache APT & Paquets Orphelins",
        "apt_desc": "Nettoyer le cache apt, les paquets orphelins et les anciens noyaux.",
        "apt_cache": "Cache APT  (/var/cache/apt)",
        "apt_autoremove": "Paquets orphelins  (autoremove)",
        "apt_autoclean": "Anciens caches  (autoclean)",
        "apt_old_kernels": "Anciens noyaux Linux",
        "apt_logs": "Anciens journaux  (/var/log/*.gz)",
        "btn_scan": "Analyser",
        "btn_clean": "Nettoyer la sélection",
        "flatpak_title": "Gestion Flatpak",
        "flatpak_desc": "Supprimer les runtimes et caches Flatpak inutilisés.",
        "flatpak_unused": "Runtimes inutilisés",
        "flatpak_cache": "Cache Flatpak  (~/.var/app/*/cache)",
        "flatpak_not_found": "Flatpak n'est pas installé sur ce système.",
        "dirs_title": "Utilisation des Répertoires Utilisateur",
        "dirs_desc": "Voir la taille des répertoires et supprimer les fichiers sélectionnés.",
        "dirs_path": "Chemin",
        "dirs_size": "Taille",
        "dirs_usage": "Utilisation",
        "btn_browse": "Parcourir",
        "btn_delete_selected": "Supprimer la sélection",
        "btn_refresh": "Actualiser",
        "tips_title": "Conseils de Performance",
        "tips_subtitle": "10 recommandations pour accélérer votre système",
        "lang_label": "Langue",
        "status_idle": "Prêt",
        "status_scanning": "Analyse…",
        "status_cleaning": "Nettoyage…",
        "status_done": "Terminé!",
        "status_error": "Erreur!",
        "confirm_clean": "Les éléments sélectionnés seront supprimés définitivement.\nContinuer?",
        "confirm_title": "Confirmer",
        "freed_space": "Espace libéré",
        "total_found": "Total trouvé",
        "no_items": "Rien à nettoyer.",
        "scanning_done": "Analyse terminée.",
        "select_all": "Tout sélectionner",
        "deselect_all": "Désélectionner tout",
        "disk_usage": "Utilisation du disque",
        "file_name": "Nom",
        "file_type": "Type",
        "confirm_delete": "Les fichiers/dossiers sélectionnés seront supprimés!\nConfirmer?",
        "deleted_ok": "Supprimé avec succès.",
        "privilege_error": "Impossible d'obtenir les droits admin. pkexec est-il installé?",
        "running_as_root": "Application lancée en administrateur.",
        "auth_cancelled": "Authentification annulée.",
        "installed_apps": "Applications Flatpak installées",
        "loading": "Chargement…",
    },
    "de": {
        "app_title": "YinegelOS Reiniger",
        "tab_dashboard": "Übersicht",
        "tab_apt": "APT-Bereinigung",
        "tab_flatpak": "Flatpak",
        "tab_userdirs": "Benutzerverzeichnisse",
        "tab_tips": "Tipps",
        "dashboard_welcome": "System Optimieren",
        "dashboard_subtitle": "Keine Bereinigung durchgeführt",
        "btn_quick_scan": "Schnellscan",
        "btn_clean_all": "Alles bereinigen",
        "apt_title": "APT-Cache & Verwaiste Pakete",
        "apt_desc": "APT-Cache, verwaiste Pakete und alte Kernel bereinigen.",
        "apt_cache": "APT-Cache  (/var/cache/apt)",
        "apt_autoremove": "Verwaiste Pakete  (autoremove)",
        "apt_autoclean": "Alte Caches  (autoclean)",
        "apt_old_kernels": "Alte Linux-Kernel",
        "apt_logs": "Alte Protokolle  (/var/log/*.gz)",
        "btn_scan": "Scannen",
        "btn_clean": "Auswahl bereinigen",
        "flatpak_title": "Flatpak-Verwaltung",
        "flatpak_desc": "Unbenutzte Flatpak-Laufzeiten und Caches entfernen.",
        "flatpak_unused": "Unbenutzte Laufzeiten",
        "flatpak_cache": "Flatpak-Cache  (~/.var/app/*/cache)",
        "flatpak_not_found": "Flatpak ist nicht auf diesem System installiert.",
        "dirs_title": "Benutzerverzeichnis-Nutzung",
        "dirs_desc": "Verzeichnisgrößen anzeigen und Dateien löschen.",
        "dirs_path": "Pfad",
        "dirs_size": "Größe",
        "dirs_usage": "Nutzung",
        "btn_browse": "Durchsuchen",
        "btn_delete_selected": "Auswahl löschen",
        "btn_refresh": "Aktualisieren",
        "tips_title": "System-Optimierungstipps",
        "tips_subtitle": "10 praktische Empfehlungen zur Systemoptimierung",
        "lang_label": "Sprache",
        "status_idle": "Bereit",
        "status_scanning": "Wird gescannt…",
        "status_cleaning": "Wird bereinigt…",
        "status_done": "Fertig!",
        "status_error": "Fehler!",
        "confirm_clean": "Ausgewählte Elemente werden dauerhaft gelöscht.\nFortfahren?",
        "confirm_title": "Bestätigen",
        "freed_space": "Freigegebener Speicher",
        "total_found": "Gesamt gefunden",
        "no_items": "Nichts zu bereinigen.",
        "scanning_done": "Scan abgeschlossen.",
        "select_all": "Alle auswählen",
        "deselect_all": "Auswahl aufheben",
        "disk_usage": "Festplattennutzung",
        "file_name": "Name",
        "file_type": "Typ",
        "confirm_delete": "Ausgewählte Dateien/Ordner werden dauerhaft gelöscht!\nBestätigen?",
        "deleted_ok": "Erfolgreich gelöscht.",
        "privilege_error": "Admin-Rechte konnten nicht erlangt werden. Ist pkexec installiert?",
        "running_as_root": "Anwendung läuft als Administrator.",
        "auth_cancelled": "Authentifizierung abgebrochen.",
        "installed_apps": "Installierte Flatpak-Apps",
        "loading": "Laden…",
    },
    "pt": {
        "app_title": "YinegelOS Limpador",
        "tab_dashboard": "Painel",
        "tab_apt": "Limpeza APT",
        "tab_flatpak": "Flatpak",
        "tab_userdirs": "Diretórios",
        "tab_tips": "Dicas",
        "dashboard_welcome": "Otimize Seu Sistema",
        "dashboard_subtitle": "Nenhuma limpeza realizada ainda",
        "btn_quick_scan": "Verificação rápida",
        "btn_clean_all": "Limpar tudo",
        "apt_title": "Cache APT & Pacotes Órfãos",
        "apt_desc": "Limpar cache apt, pacotes órfãos e kernels antigos.",
        "apt_cache": "Cache APT  (/var/cache/apt)",
        "apt_autoremove": "Pacotes Órfãos  (autoremove)",
        "apt_autoclean": "Caches Antigos  (autoclean)",
        "apt_old_kernels": "Kernels Linux Antigos",
        "apt_logs": "Logs Antigos  (/var/log/*.gz)",
        "btn_scan": "Verificar",
        "btn_clean": "Limpar Selecionados",
        "flatpak_title": "Gerenciamento Flatpak",
        "flatpak_desc": "Remover runtimes e caches Flatpak não utilizados.",
        "flatpak_unused": "Runtimes Não Utilizados",
        "flatpak_cache": "Cache Flatpak  (~/.var/app/*/cache)",
        "flatpak_not_found": "Flatpak não está instalado neste sistema.",
        "dirs_title": "Uso de Diretórios do Usuário",
        "dirs_desc": "Ver tamanho dos diretórios e excluir arquivos selecionados.",
        "dirs_path": "Caminho",
        "dirs_size": "Tamanho",
        "dirs_usage": "Uso",
        "btn_browse": "Navegar",
        "btn_delete_selected": "Excluir Selecionados",
        "btn_refresh": "Atualizar",
        "tips_title": "Dicas de Velocidade",
        "tips_subtitle": "10 recomendações práticas para acelerar seu sistema",
        "lang_label": "Idioma",
        "status_idle": "Pronto",
        "status_scanning": "Verificando…",
        "status_cleaning": "Limpando…",
        "status_done": "Concluído!",
        "status_error": "Erro!",
        "confirm_clean": "Os itens selecionados serão excluídos permanentemente.\nContinuar?",
        "confirm_title": "Confirmar",
        "freed_space": "Espaço liberado",
        "total_found": "Total encontrado",
        "no_items": "Nada para limpar.",
        "scanning_done": "Verificação concluída.",
        "select_all": "Selecionar tudo",
        "deselect_all": "Desmarcar tudo",
        "disk_usage": "Uso do Disco",
        "file_name": "Nome",
        "file_type": "Tipo",
        "confirm_delete": "Arquivos/pastas selecionados serão excluídos permanentemente!\nConfirmar?",
        "deleted_ok": "Excluído com sucesso.",
        "privilege_error": "Não foi possível obter privilégios de admin. pkexec está instalado?",
        "running_as_root": "Aplicação rodando como administrador.",
        "auth_cancelled": "Autenticação cancelada.",
        "installed_apps": "Aplicativos Flatpak Instalados",
        "loading": "Carregando…",
    },
}

SPEED_TIPS = {
    "tr": [
        ("🚀", "Önyükleme Süresini Kısalt",
         "systemd-analyze blame\n\nEn uzun süre alan servisleri listeler. "
         "Gereksiz olanları devre dışı bırakın:\n  sudo systemctl disable <servis-adı>"),
        ("💾", "Swap Kullanımını Optimize Et",
         "echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf\nsudo sysctl -p\n\n"
         "RAM dolmadan swap kullanımını geciktirir."),
        ("🗑️", "Journald Log Boyutunu Sınırla",
         "sudo journalctl --vacuum-size=200M\n\n"
         "/etc/systemd/journald.conf içine ekleyin:\n  SystemMaxUse=200M"),
        ("🔄", "Preload ile Hızlı Uygulama Aç",
         "sudo apt install preload\nsudo systemctl enable preload --now\n\n"
         "Sık açılan uygulamaları RAM'e önceden yükler."),
        ("🧹", "Gereksiz Servisleri Kapat",
         "systemctl list-units --type=service --state=running\n\n"
         "Listedeki gereksiz servisleri durdurun:\n  sudo systemctl disable --now <servis>"),
        ("📦", "Snap Paketlerini Flatpak ile Değiştir",
         "sudo systemctl disable snapd --now\nsudo apt purge snapd\n\n"
         "Snap paketleri yavaş başlar; Flatpak daha hızlıdır."),
        ("⚡", "Zram ile Bellek Kapasitesini Artır",
         "sudo apt install zram-tools\n\n"
         "/etc/default/zramswap içinde:\n  ALGO=lz4\n  PERCENT=50"),
        ("🖥️", "Nvidia GPU Performansını Artır",
         "nvidia-settings\n→ PowerMizer → Prefer Maximum Performance\n\n"
         "Veya kalıcı olarak:\n  sudo nvidia-smi -pm 1"),
        ("📁", "Dosya Sistemi Önbelleğini Temizle",
         "sudo sync && sudo sysctl -w vm.drop_caches=3\n\n"
         "RAM'i anlık olarak serbest bırakır (otomatik dolacaktır)."),
        ("🔧", "TLP ile Pil & CPU Optimizasyonu",
         "sudo apt install tlp tlp-rdw\nsudo systemctl enable tlp --now\n\n"
         "Dizüstü bilgisayarlarda pil ömrünü ve tepki süresini iyileştirir."),
    ],
    "en": [
        ("🚀", "Reduce Boot Time",
         "systemd-analyze blame\n\nLists slowest services. Disable unnecessary ones:\n  sudo systemctl disable <service>"),
        ("💾", "Optimize Swap Usage",
         "echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf\nsudo sysctl -p\n\nDelays swap use until RAM is nearly full."),
        ("🗑️", "Limit Journald Log Size",
         "sudo journalctl --vacuum-size=200M\n\nAdd to /etc/systemd/journald.conf:\n  SystemMaxUse=200M"),
        ("🔄", "Preload Apps Faster",
         "sudo apt install preload\nsudo systemctl enable preload --now\n\nPre-loads frequently used apps into RAM."),
        ("🧹", "Disable Unused Services",
         "systemctl list-units --type=service --state=running\n\nStop unnecessary services:\n  sudo systemctl disable --now <service>"),
        ("📦", "Replace Snap with Flatpak",
         "sudo systemctl disable snapd --now\nsudo apt purge snapd\n\nSnap starts slower; Flatpak is faster."),
        ("⚡", "Expand Memory with Zram",
         "sudo apt install zram-tools\n\nIn /etc/default/zramswap:\n  ALGO=lz4\n  PERCENT=50"),
        ("🖥️", "Boost Nvidia GPU Performance",
         "nvidia-settings\n→ PowerMizer → Prefer Maximum Performance\n\nOr permanently:\n  sudo nvidia-smi -pm 1"),
        ("📁", "Clear Filesystem Cache",
         "sudo sync && sudo sysctl -w vm.drop_caches=3\n\nFrees RAM instantly (kernel will repopulate automatically)."),
        ("🔧", "Battery & CPU with TLP",
         "sudo apt install tlp tlp-rdw\nsudo systemctl enable tlp --now\n\nImproves battery life and responsiveness on laptops."),
    ],
    "fr": [
        ("🚀","Réduire le Démarrage","systemd-analyze blame\n\nListe les services lents. Désactivez les inutiles:\n  sudo systemctl disable <service>"),
        ("💾","Optimiser le Swap","echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf\nsudo sysctl -p"),
        ("🗑️","Limiter les Journaux","sudo journalctl --vacuum-size=200M\n\nAjoutez dans journald.conf:\n  SystemMaxUse=200M"),
        ("🔄","Précharger les Apps","sudo apt install preload\nsudo systemctl enable preload --now"),
        ("🧹","Désactiver Services Inutiles","systemctl list-units --type=service --state=running"),
        ("📦","Remplacer Snap par Flatpak","sudo systemctl disable snapd --now\nsudo apt purge snapd"),
        ("⚡","Mémoire avec Zram","sudo apt install zram-tools\n\n/etc/default/zramswap:\n  ALGO=lz4\n  PERCENT=50"),
        ("🖥️","Performances GPU Nvidia","nvidia-settings → PowerMizer → Prefer Maximum Performance"),
        ("📁","Vider le Cache FS","sudo sync && sudo sysctl -w vm.drop_caches=3"),
        ("🔧","TLP pour la Batterie","sudo apt install tlp tlp-rdw\nsudo systemctl enable tlp --now"),
    ],
    "de": [
        ("🚀","Startzeit Reduzieren","systemd-analyze blame\n\nDeaktivieren Sie langsame Dienste:\n  sudo systemctl disable <Dienst>"),
        ("💾","Swap Optimieren","echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf\nsudo sysctl -p"),
        ("🗑️","Protokolle Begrenzen","sudo journalctl --vacuum-size=200M\n\nIn journald.conf:\n  SystemMaxUse=200M"),
        ("🔄","Apps Vorladen","sudo apt install preload\nsudo systemctl enable preload --now"),
        ("🧹","Dienste Deaktivieren","systemctl list-units --type=service --state=running"),
        ("📦","Snap durch Flatpak Ersetzen","sudo systemctl disable snapd --now\nsudo apt purge snapd"),
        ("⚡","Zram Speicher","sudo apt install zram-tools\n\n/etc/default/zramswap:\n  ALGO=lz4\n  PERCENT=50"),
        ("🖥️","Nvidia GPU","nvidia-settings → PowerMizer → Prefer Maximum Performance"),
        ("📁","FS-Cache Leeren","sudo sync && sudo sysctl -w vm.drop_caches=3"),
        ("🔧","TLP Akku","sudo apt install tlp tlp-rdw\nsudo systemctl enable tlp --now"),
    ],
    "pt": [
        ("🚀","Reduzir Boot","systemd-analyze blame\n\nDesative serviços desnecessários:\n  sudo systemctl disable <serviço>"),
        ("💾","Otimizar Swap","echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf\nsudo sysctl -p"),
        ("🗑️","Limitar Logs","sudo journalctl --vacuum-size=200M\n\nEm journald.conf:\n  SystemMaxUse=200M"),
        ("🔄","Preload","sudo apt install preload\nsudo systemctl enable preload --now"),
        ("🧹","Desativar Serviços","systemctl list-units --type=service --state=running"),
        ("📦","Substituir Snap","sudo systemctl disable snapd --now\nsudo apt purge snapd"),
        ("⚡","Zram","sudo apt install zram-tools\n\n/etc/default/zramswap:\n  ALGO=lz4\n  PERCENT=50"),
        ("🖥️","Nvidia GPU","nvidia-settings → PowerMizer → Prefer Maximum Performance"),
        ("📁","Limpar Cache","sudo sync && sudo sysctl -w vm.drop_caches=3"),
        ("🔧","TLP","sudo apt install tlp tlp-rdw\nsudo systemctl enable tlp --now"),
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
# YARDIMCI FONKSİYONLAR
# ─────────────────────────────────────────────────────────────────────────────

def format_size(size_bytes: int) -> str:
    if size_bytes <= 0:
        return "0 B"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def get_dir_size(path) -> int:
    try:
        result = subprocess.run(
            ["du", "-sb", str(path)],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            return int(result.stdout.split()[0])
    except Exception:
        pass
    total = 0
    try:
        for dp, _, files in os.walk(str(path)):
            for f in files:
                try:
                    total += os.path.getsize(os.path.join(dp, f))
                except OSError:
                    pass
    except OSError:
        pass
    return total


def get_disk_usage():
    try:
        u = shutil.disk_usage("/")
        return u.total, u.used, u.free
    except Exception:
        return 0, 0, 0


def run_cmd(args: list, timeout=60) -> tuple[bool, str, str]:
    """Normal (kullanıcı yetkili) komut çalıştırır."""
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, r.stdout, r.stderr
    except Exception as e:
        return False, "", str(e)


def run_privileged(args: list, timeout=120) -> tuple[bool, str, str]:
    """
    Yönetici yetkisi gerektiren komutları çalıştırır.
    Önce zaten root olup olmadığını kontrol eder.
    Değilse pkexec ile GUI şifre istemi açar.
    pkexec yoksa sudo -A dener.
    """
    # Zaten root?
    if os.geteuid() == 0:
        return run_cmd(args, timeout)

    # pkexec dene
    pkexec = shutil.which("pkexec")
    if pkexec:
        try:
            r = subprocess.run(
                [pkexec] + args,
                capture_output=True, text=True, timeout=timeout
            )
            # pkexec iptal kodu: 126
            if r.returncode == 126:
                return False, "", "AUTH_CANCELLED"
            return r.returncode == 0, r.stdout, r.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Timeout"
        except Exception as e:
            return False, "", str(e)

    # Fallback: sudo (terminal varsa çalışır)
    sudo = shutil.which("sudo")
    if sudo:
        try:
            r = subprocess.run(
                [sudo, "-n"] + args,
                capture_output=True, text=True, timeout=timeout
            )
            return r.returncode == 0, r.stdout, r.stderr
        except Exception as e:
            return False, "", str(e)

    return False, "", "NO_PRIV_TOOL"


def check_flatpak() -> bool:
    ok, _, _ = run_cmd(["flatpak", "--version"])
    return ok


def get_apt_cache_size() -> int:
    return get_dir_size("/var/cache/apt/archives")


def get_log_size() -> int:
    return get_dir_size("/var/log")


def get_flatpak_cache_size() -> int:
    base = Path.home() / ".var" / "app"
    if not base.exists():
        return 0
    total = 0
    for app_dir in base.iterdir():
        cache = app_dir / "cache"
        if cache.exists():
            total += get_dir_size(cache)
    return total


# ─────────────────────────────────────────────────────────────────────────────
# ANA PENCERE
# ─────────────────────────────────────────────────────────────────────────────

class App:

    COLORS = {
        "bg":       "#0d0d1a",
        "card":     "#14142a",
        "card2":    "#1c1c35",
        "border":   "#252540",
        "accent":   "#6c63ff",
        "accent_h": "#5248d4",
        "success":  "#3ecf8e",
        "warning":  "#f59e0b",
        "danger":   "#ef4444",
        "danger_h": "#b91c1c",
        "text":     "#e2e2f0",
        "sub":      "#7878a0",
    }

    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("YinegelOS Temizleyici")
        self.root.geometry("1020x720")
        self.root.minsize(900, 620)
        self.root.configure(fg_color=self.COLORS["bg"])

        self._lang = "tr"
        self._T    = TRANSLATIONS[self._lang]

        # Widget referansları (sekme yeniden oluşturulduğunda temizlenir)
        self._dir_scroll_ref  = None   # mevcut CTkScrollableFrame
        self._dir_scan_token  = 0      # her yeni taramada artar → eski thread iptal edilir
        self._dir_items       = []
        self._dir_check_vars  = []

        self._apt_lbl_refs    = {}     # key → CTkLabel
        self._apt_check_vars  = {}     # key → BooleanVar

        self._fp_vars         = {}
        self._fp_list_box     = None

        self._build_chrome()
        self._show_tab("dashboard")
        self.root.mainloop()

    # ── çeviri ──────────────────────────────────────────────────────────────

    def t(self, key: str) -> str:
        return self._T.get(key, key)

    def _switch_lang(self, code: str):
        self._lang = code
        self._T    = TRANSLATIONS[code]
        # tüm chrome'u yeniden oluştur
        for w in self.root.winfo_children():
            w.destroy()
        self._build_chrome()
        self._show_tab("dashboard")

    # ── chrome ──────────────────────────────────────────────────────────────

    def _build_chrome(self):
        C = self.COLORS
        # Header
        hdr = ctk.CTkFrame(self.root, fg_color=C["card"], corner_radius=0, height=60)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        ctk.CTkLabel(
            hdr, text="⟁  " + self.t("app_title"),
            font=ctk.CTkFont("Monospace", 19, "bold"),
            text_color=C["accent"]
        ).pack(side="left", padx=22)

        # pkexec / root durumu
        root_badge = "🔒 root" if os.geteuid() == 0 else ("🔑 pkexec" if shutil.which("pkexec") else "⚠️ no-priv")
        ctk.CTkLabel(hdr, text=root_badge,
                     font=ctk.CTkFont(size=11),
                     text_color=C["success"] if os.geteuid() == 0 else C["sub"]
                     ).pack(side="right", padx=6)

        # Dil bayrakları
        lf = ctk.CTkFrame(hdr, fg_color="transparent")
        lf.pack(side="right", padx=8)
        ctk.CTkLabel(lf, text=self.t("lang_label"),
                     text_color=C["sub"], font=ctk.CTkFont(size=11)
                     ).pack(side="left", padx=(0, 6))
        for code, flag in [("tr","🇹🇷"),("en","🇬🇧"),("fr","🇫🇷"),("de","🇩🇪"),("pt","🇵🇹")]:
            ctk.CTkButton(
                lf, text=flag, width=34, height=28, corner_radius=6,
                font=ctk.CTkFont(size=15),
                fg_color=C["accent"] if self._lang == code else C["card2"],
                hover_color=C["accent"],
                command=lambda c=code: self._switch_lang(c)
            ).pack(side="left", padx=2)

        # Body
        body = ctk.CTkFrame(self.root, fg_color="transparent")
        body.pack(fill="both", expand=True)

        # Sidebar
        self._sidebar = ctk.CTkFrame(body, fg_color=C["card"], corner_radius=0, width=198)
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)

        self._tab_btns: dict[str, ctk.CTkButton] = {}
        tabs = [
            ("dashboard", "🏠  " + self.t("tab_dashboard")),
            ("apt",       "📦  " + self.t("tab_apt")),
            ("flatpak",   "📱  " + self.t("tab_flatpak")),
            ("userdirs",  "📂  " + self.t("tab_userdirs")),
            ("tips",      "💡  " + self.t("tab_tips")),
        ]
        ctk.CTkFrame(self._sidebar, height=12, fg_color="transparent").pack()
        for key, label in tabs:
            b = ctk.CTkButton(
                self._sidebar, text=label, anchor="w", height=42,
                fg_color="transparent", hover_color=C["card2"],
                text_color=C["text"], font=ctk.CTkFont(size=13),
                corner_radius=0,
                command=lambda k=key: self._show_tab(k)
            )
            b.pack(fill="x", padx=6, pady=1)
            self._tab_btns[key] = b

        # Status
        self._status_var = ctk.StringVar(value=self.t("status_idle"))
        ctk.CTkLabel(
            self._sidebar, textvariable=self._status_var,
            text_color=C["sub"], font=ctk.CTkFont(size=11), wraplength=175
        ).pack(side="bottom", padx=10, pady=10)

        # Content
        self._content = ctk.CTkFrame(body, fg_color=C["bg"], corner_radius=0)
        self._content.pack(side="left", fill="both", expand=True)

    def _show_tab(self, key: str):
        C = self.COLORS
        for k, b in self._tab_btns.items():
            b.configure(fg_color=C["accent"] if k == key else "transparent")
        # İçeriği temizle — dir_scroll referansını da sıfırla
        self._dir_scroll_ref = None
        self._dir_scan_token += 1      # arka plan thread'ini geçersiz kıl
        for w in self._content.winfo_children():
            w.destroy()
        getattr(self, f"_tab_{key}")()

    def _status(self, msg: str):
        self._status_var.set(msg)

    # ── Yardımcı: log textbox'a yaz ─────────────────────────────────────────

    def _log_write(self, tb: ctk.CTkTextbox, msg: str):
        """Thread-safe log satırı ekler. tb None ise sessizce atlar."""
        if tb is None:
            return
        try:
            tb.configure(state="normal")
            tb.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
            tb.see("end")
            tb.configure(state="disabled")
        except Exception:
            pass

    # ═════════════════════════════════════════════════════════════════════════
    # SEKME: DASHBOARD
    # ═════════════════════════════════════════════════════════════════════════

    def _tab_dashboard(self):
        C = self.COLORS
        frame = ctk.CTkScrollableFrame(self._content, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=26, pady=20)

        ctk.CTkLabel(frame, text=self.t("dashboard_welcome"),
                     font=ctk.CTkFont(size=26, weight="bold"),
                     text_color=C["text"]).pack(anchor="w")
        ctk.CTkLabel(frame, text=self.t("dashboard_subtitle"),
                     font=ctk.CTkFont(size=13), text_color=C["sub"]).pack(anchor="w", pady=(2,14))

        # Disk kartı
        total, used, free = get_disk_usage()
        dc = ctk.CTkFrame(frame, fg_color=C["card"], corner_radius=14)
        dc.pack(fill="x", pady=6)
        ctk.CTkLabel(dc, text="💿  " + self.t("disk_usage"),
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=C["accent"]).pack(anchor="w", padx=18, pady=(14,4))
        row = ctk.CTkFrame(dc, fg_color="transparent")
        row.pack(fill="x", padx=18)
        for label, val, col in [
            ("Toplam", format_size(total), C["text"]),
            ("Kullanılan", format_size(used), C["warning"]),
            ("Boş", format_size(free), C["success"]),
        ]:
            cc = ctk.CTkFrame(row, fg_color=C["card2"], corner_radius=8)
            cc.pack(side="left", padx=(0,10), pady=6, ipadx=14, ipady=8)
            ctk.CTkLabel(cc, text=val, font=ctk.CTkFont(size=17, weight="bold"),
                         text_color=col).pack()
            ctk.CTkLabel(cc, text=label, font=ctk.CTkFont(size=10),
                         text_color=C["sub"]).pack()
        pct = (used / total) if total > 0 else 0
        pb = ctk.CTkProgressBar(dc, height=8, corner_radius=4,
                                 progress_color=C["warning"] if pct > 0.8 else C["accent"],
                                 fg_color=C["card2"])
        pb.pack(fill="x", padx=18, pady=(6,16))
        pb.set(pct)

        # Mini kartlar
        mr = ctk.CTkFrame(frame, fg_color="transparent")
        mr.pack(fill="x", pady=6)
        for icon, lbl, size, col in [
            ("📦", "APT Cache", get_apt_cache_size(), C["accent"]),
            ("📋", "Sys Logs",  get_log_size(),       C["warning"]),
            ("📱", "Flatpak",   get_flatpak_cache_size() if check_flatpak() else 0, C["sub"]),
        ]:
            mc = ctk.CTkFrame(mr, fg_color=C["card"], corner_radius=12)
            mc.pack(side="left", expand=True, fill="x", padx=(0,8), ipadx=8, ipady=10)
            ctk.CTkLabel(mc, text=icon, font=ctk.CTkFont(size=26)).pack()
            ctk.CTkLabel(mc, text=format_size(size),
                         font=ctk.CTkFont(size=17, weight="bold"), text_color=col).pack()
            ctk.CTkLabel(mc, text=lbl, font=ctk.CTkFont(size=10), text_color=C["sub"]).pack()

        # Butonlar
        br = ctk.CTkFrame(frame, fg_color="transparent")
        br.pack(pady=16)
        ctk.CTkButton(br, text="🔍  " + self.t("btn_quick_scan"),
                      fg_color=C["card2"], hover_color=C["accent"],
                      height=42, width=190, corner_radius=10,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=lambda: threading.Thread(
                          target=self._do_dash_scan, args=(dash_log,), daemon=True).start()
                      ).pack(side="left", padx=8)
        ctk.CTkButton(br, text="🧹  " + self.t("btn_clean_all"),
                      fg_color=C["danger"], hover_color=C["danger_h"],
                      height=42, width=190, corner_radius=10,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=lambda: self._confirm_and_run(
                          lambda: threading.Thread(
                              target=self._do_clean_all, args=(dash_log,), daemon=True).start())
                      ).pack(side="left", padx=8)

        # Log kutusu
        dash_log = ctk.CTkTextbox(frame, height=130, fg_color=C["card"],
                                   text_color=C["sub"],
                                   font=ctk.CTkFont("Monospace", 11),
                                   corner_radius=10, border_width=0, state="disabled")
        dash_log.pack(fill="x", pady=(4,0))
        self._log_write(dash_log, "# YinegelOS Temizleyici v2 hazır.")
        if os.geteuid() == 0:
            self._log_write(dash_log, "# " + self.t("running_as_root"))
        elif shutil.which("pkexec"):
            self._log_write(dash_log, "# pkexec bulundu — yönetici işlemler GUI şifresi isteyecek.")
        else:
            self._log_write(dash_log, "# UYARI: pkexec bulunamadı. APT temizleme çalışmayabilir.")

    def _do_dash_scan(self, tb):
        self.root.after(0, lambda: self._status(self.t("status_scanning")))
        apt = get_apt_cache_size()
        log = get_log_size()
        fp  = get_flatpak_cache_size() if check_flatpak() else 0
        total = apt + log + fp
        self.root.after(0, lambda: self._log_write(tb, f"APT Cache : {format_size(apt)}"))
        self.root.after(0, lambda: self._log_write(tb, f"Sys Logs  : {format_size(log)}"))
        if fp:
            self.root.after(0, lambda: self._log_write(tb, f"Flatpak   : {format_size(fp)}"))
        self.root.after(0, lambda: self._log_write(tb, f"─── Toplam: {format_size(total)} ───"))
        self.root.after(0, lambda: self._status(self.t("status_done")))

    def _do_clean_all(self, tb):
        self.root.after(0, lambda: self._status(self.t("status_cleaning")))
        for cmd, label in [
            (["apt-get", "autoclean", "-y"],    "apt autoclean"),
            (["apt-get", "autoremove", "-y"],   "apt autoremove"),
        ]:
            ok, out, err = run_privileged(cmd)
            msg = ("✓ " if ok else "✗ ") + label
            if not ok and err == "AUTH_CANCELLED":
                msg = "⚠ " + self.t("auth_cancelled")
            self.root.after(0, lambda m=msg: self._log_write(tb, m))

        if check_flatpak():
            ok, _, _ = run_cmd(["flatpak", "uninstall", "--unused", "-y"])
            msg = ("✓ " if ok else "✗ ") + "flatpak --unused"
            self.root.after(0, lambda m=msg: self._log_write(tb, m))

        self.root.after(0, lambda: self._status(self.t("status_done")))
        self.root.after(0, lambda: self._log_write(tb, "✅ " + self.t("status_done")))

    def _confirm_and_run(self, fn):
        if messagebox.askyesno(self.t("confirm_title"), self.t("confirm_clean")):
            fn()

    # ═════════════════════════════════════════════════════════════════════════
    # SEKME: APT
    # ═════════════════════════════════════════════════════════════════════════

    def _tab_apt(self):
        C = self.COLORS
        self._apt_check_vars = {}
        self._apt_lbl_refs   = {}

        frame = ctk.CTkScrollableFrame(self._content, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=26, pady=20)

        ctk.CTkLabel(frame, text="📦  " + self.t("apt_title"),
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=C["text"]).pack(anchor="w")
        ctk.CTkLabel(frame, text=self.t("apt_desc"),
                     font=ctk.CTkFont(size=12), text_color=C["sub"]).pack(anchor="w", pady=(2,14))

        items = [
            ("apt_cache",      self.t("apt_cache"),      "/var/cache/apt/archives"),
            ("apt_autoremove", self.t("apt_autoremove"),  "apt-get autoremove"),
            ("apt_autoclean",  self.t("apt_autoclean"),   "apt-get autoclean"),
            ("apt_old_kernels",self.t("apt_old_kernels"), "dpkg --list | grep linux-image"),
            ("apt_logs",       self.t("apt_logs"),        "/var/log/*.gz  *.1  *.old"),
        ]
        for key, label, path in items:
            row = ctk.CTkFrame(frame, fg_color=C["card"], corner_radius=10)
            row.pack(fill="x", pady=4)
            var = ctk.BooleanVar(value=False)
            self._apt_check_vars[key] = var
            ctk.CTkCheckBox(row, text=label, variable=var,
                            font=ctk.CTkFont(size=13), text_color=C["text"],
                            fg_color=C["accent"], hover_color=C["accent_h"]
                            ).pack(side="left", padx=16, pady=13)
            size_lbl = ctk.CTkLabel(row, text="—", font=ctk.CTkFont(size=12), text_color=C["sub"])
            size_lbl.pack(side="right", padx=14)
            self._apt_lbl_refs[key] = size_lbl
            ctk.CTkLabel(row, text=path, font=ctk.CTkFont("Monospace", 10),
                         text_color=C["sub"]).pack(side="right", padx=6)

        br = ctk.CTkFrame(frame, fg_color="transparent")
        br.pack(pady=14)
        apt_log = ctk.CTkTextbox(frame, height=145, fg_color=C["card"],
                                  text_color=C["sub"], font=ctk.CTkFont("Monospace", 11),
                                  corner_radius=10, border_width=0, state="disabled")
        apt_log.pack(fill="x")
        self._log_write(apt_log, "# APT paneli hazır.")

        ctk.CTkButton(br, text="🔍  " + self.t("btn_scan"),
                      fg_color=C["card2"], hover_color=C["accent"],
                      height=40, width=150, corner_radius=8,
                      command=lambda: threading.Thread(
                          target=self._do_apt_scan, args=(apt_log,), daemon=True).start()
                      ).pack(side="left", padx=8)
        ctk.CTkButton(br, text="🧹  " + self.t("btn_clean"),
                      fg_color=C["accent"], hover_color=C["accent_h"],
                      height=40, width=170, corner_radius=8,
                      command=lambda: self._apt_clean(apt_log)
                      ).pack(side="left", padx=8)

    def _do_apt_scan(self, tb):
        self.root.after(0, lambda: self._status(self.t("status_scanning")))
        sizes = {
            "apt_cache": get_apt_cache_size(),
            "apt_logs":  get_log_size(),
        }
        for key, sz in sizes.items():
            s = format_size(sz)
            def _upd(k=key, v=s):
                if k in self._apt_lbl_refs:
                    try:
                        self._apt_lbl_refs[k].configure(text=v)
                    except Exception:
                        pass
            self.root.after(0, _upd)

        # dry-run autoremove
        ok, out, _ = run_privileged(["apt-get", "--dry-run", "autoremove"])
        if ok and out:
            for line in out.splitlines():
                stripped = line.strip()
                if stripped:
                    self.root.after(0, lambda l=stripped: self._log_write(tb, l))

        self.root.after(0, lambda: self._status(self.t("scanning_done")))
        self.root.after(0, lambda: self._log_write(tb, "✓ " + self.t("scanning_done")))

    def _apt_clean(self, tb):
        selected = [k for k, v in self._apt_check_vars.items() if v.get()]
        if not selected:
            messagebox.showinfo(self.t("confirm_title"), self.t("no_items"))
            return
        if not messagebox.askyesno(self.t("confirm_title"), self.t("confirm_clean")):
            return
        threading.Thread(target=self._do_apt_clean, args=(selected, tb), daemon=True).start()

    def _do_apt_clean(self, selected, tb):
        self.root.after(0, lambda: self._status(self.t("status_cleaning")))
        for key in selected:
            if key == "apt_cache":
                ok, _, err = run_privileged(["apt-get", "clean"])
                msg = ("✓" if ok else ("⚠ " + self.t("auth_cancelled") if err == "AUTH_CANCELLED" else "✗")) + " apt-get clean"
            elif key == "apt_autoremove":
                ok, _, err = run_privileged(["apt-get", "autoremove", "-y"])
                msg = ("✓" if ok else "✗") + " apt-get autoremove"
            elif key == "apt_autoclean":
                ok, _, err = run_privileged(["apt-get", "autoclean", "-y"])
                msg = ("✓" if ok else "✗") + " apt-get autoclean"
            elif key == "apt_old_kernels":
                # Eski kernelleri bul ve kaldır
                ok, out, _ = run_cmd(["dpkg", "--list"])
                current = subprocess.run(["uname", "-r"], capture_output=True, text=True).stdout.strip()
                removed = 0
                if ok:
                    for line in out.splitlines():
                        if "linux-image-" in line and current not in line and line.startswith("ii"):
                            pkg = line.split()[1]
                            r, _, _ = run_privileged(["apt-get", "purge", "-y", pkg])
                            if r:
                                removed += 1
                msg = f"✓ {removed} eski kernel kaldırıldı" if removed else "— eski kernel bulunamadı"
            elif key == "apt_logs":
                ok1, _, _ = run_privileged(["find", "/var/log", "-name", "*.gz", "-delete"])
                ok2, _, _ = run_privileged(["find", "/var/log", "-name", "*.1", "-delete"])
                ok3, _, _ = run_privileged(["find", "/var/log", "-name", "*.old", "-delete"])
                msg = ("✓" if (ok1 or ok2 or ok3) else "✗") + " eski log dosyaları silindi"
            else:
                continue
            self.root.after(0, lambda m=msg: self._log_write(tb, m))

        self.root.after(0, lambda: self._status(self.t("status_done")))
        self.root.after(0, lambda: self._log_write(tb, "✅ " + self.t("status_done")))

    # ═════════════════════════════════════════════════════════════════════════
    # SEKME: FLATPAK
    # ═════════════════════════════════════════════════════════════════════════

    def _tab_flatpak(self):
        C = self.COLORS
        self._fp_vars    = {}
        self._fp_list_box = None

        frame = ctk.CTkScrollableFrame(self._content, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=26, pady=20)

        ctk.CTkLabel(frame, text="📱  " + self.t("flatpak_title"),
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=C["text"]).pack(anchor="w")
        ctk.CTkLabel(frame, text=self.t("flatpak_desc"),
                     font=ctk.CTkFont(size=12), text_color=C["sub"]).pack(anchor="w", pady=(2,14))

        if not check_flatpak():
            ctk.CTkLabel(frame, text="⚠️  " + self.t("flatpak_not_found"),
                         font=ctk.CTkFont(size=14), text_color=C["warning"]).pack(pady=40)
            return

        for key, label in [("fp_unused", self.t("flatpak_unused")),
                            ("fp_cache",  self.t("flatpak_cache"))]:
            row = ctk.CTkFrame(frame, fg_color=C["card"], corner_radius=10)
            row.pack(fill="x", pady=4)
            var = ctk.BooleanVar(value=False)
            self._fp_vars[key] = var
            ctk.CTkCheckBox(row, text=label, variable=var,
                            font=ctk.CTkFont(size=13), text_color=C["text"],
                            fg_color=C["accent"], hover_color=C["accent_h"]
                            ).pack(side="left", padx=16, pady=13)
            sz_lbl = ctk.CTkLabel(row, text="—", font=ctk.CTkFont(size=12), text_color=C["sub"])
            sz_lbl.pack(side="right", padx=14)
            self._fp_vars[key + "_lbl"] = sz_lbl

        ctk.CTkLabel(frame, text=self.t("installed_apps"),
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=C["text"]).pack(anchor="w", pady=(14,4))
        fp_list = ctk.CTkTextbox(frame, height=140, fg_color=C["card"],
                                  text_color=C["sub"], font=ctk.CTkFont("Monospace", 11),
                                  corner_radius=10)
        fp_list.pack(fill="x")
        fp_list.insert("end", self.t("loading"))
        self._fp_list_box = fp_list

        br = ctk.CTkFrame(frame, fg_color="transparent")
        br.pack(pady=12)
        fp_log = ctk.CTkTextbox(frame, height=100, fg_color=C["card"],
                                 text_color=C["sub"], font=ctk.CTkFont("Monospace", 11),
                                 corner_radius=10, border_width=0, state="disabled")
        fp_log.pack(fill="x", pady=(6,0))

        ctk.CTkButton(br, text="🔍  " + self.t("btn_scan"),
                      fg_color=C["card2"], hover_color=C["accent"],
                      height=40, width=150, corner_radius=8,
                      command=lambda: threading.Thread(
                          target=self._do_fp_scan, args=(fp_log,), daemon=True).start()
                      ).pack(side="left", padx=8)
        ctk.CTkButton(br, text="🧹  " + self.t("btn_clean"),
                      fg_color=C["accent"], hover_color=C["accent_h"],
                      height=40, width=170, corner_radius=8,
                      command=lambda: self._fp_clean(fp_log)
                      ).pack(side="left", padx=8)

        # Otomatik listele
        threading.Thread(target=self._fp_load_list, daemon=True).start()

    def _fp_load_list(self):
        ok, out, _ = run_cmd(["flatpak", "list", "--app", "--columns=application,name,size"])
        def _upd():
            tb = self._fp_list_box
            if tb is None:
                return
            try:
                tb.delete("1.0", "end")
                tb.insert("end", out if (ok and out.strip()) else "—")
            except Exception:
                pass
        self.root.after(0, _upd)

    def _do_fp_scan(self, tb):
        self.root.after(0, lambda: self._status(self.t("status_scanning")))
        cache_sz = get_flatpak_cache_size()
        s = format_size(cache_sz)
        def _upd():
            lbl = self._fp_vars.get("fp_cache_lbl")
            if lbl:
                try:
                    lbl.configure(text=s)
                except Exception:
                    pass
        self.root.after(0, _upd)
        self.root.after(0, lambda: self._log_write(tb, f"Flatpak cache: {s}"))
        self.root.after(0, lambda: self._status(self.t("scanning_done")))

    def _fp_clean(self, tb):
        selected = [k for k in ("fp_unused","fp_cache") if self._fp_vars.get(k) and self._fp_vars[k].get()]
        if not selected:
            messagebox.showinfo(self.t("confirm_title"), self.t("no_items"))
            return
        if not messagebox.askyesno(self.t("confirm_title"), self.t("confirm_clean")):
            return
        threading.Thread(target=self._do_fp_clean, args=(selected, tb), daemon=True).start()

    def _do_fp_clean(self, selected, tb):
        self.root.after(0, lambda: self._status(self.t("status_cleaning")))
        for key in selected:
            if key == "fp_unused":
                ok, out, _ = run_cmd(["flatpak", "uninstall", "--unused", "-y"])
                msg = ("✓" if ok else "✗") + " flatpak uninstall --unused"
                self.root.after(0, lambda m=msg: self._log_write(tb, m))
            elif key == "fp_cache":
                base = Path.home() / ".var" / "app"
                freed = 0
                if base.exists():
                    for app_dir in base.iterdir():
                        cache = app_dir / "cache"
                        if cache.exists():
                            try:
                                freed += get_dir_size(cache)
                                shutil.rmtree(cache)
                                cache.mkdir()
                            except Exception as e:
                                err = str(e)
                                self.root.after(0, lambda em=err: self._log_write(tb, f"✗ {em}"))
                f = format_size(freed)
                self.root.after(0, lambda v=f: self._log_write(tb, f"✓ Flatpak cache: {v} temizlendi"))
        self.root.after(0, lambda: self._status(self.t("status_done")))

    # ═════════════════════════════════════════════════════════════════════════
    # SEKME: KULLANICI DİZİNLERİ
    # ═════════════════════════════════════════════════════════════════════════

    def _tab_userdirs(self):
        C = self.COLORS

        outer = ctk.CTkFrame(self._content, fg_color="transparent")
        outer.pack(fill="both", expand=True, padx=26, pady=20)

        ctk.CTkLabel(outer, text="📂  " + self.t("dirs_title"),
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=C["text"]).pack(anchor="w")
        ctk.CTkLabel(outer, text=self.t("dirs_desc"),
                     font=ctk.CTkFont(size=12), text_color=C["sub"]).pack(anchor="w", pady=(2,10))

        # Yol girişi
        top = ctk.CTkFrame(outer, fg_color=C["card"], corner_radius=10)
        top.pack(fill="x", pady=(0,6))
        self._dir_path_var = ctk.StringVar(value=str(Path.home()))
        ctk.CTkEntry(top, textvariable=self._dir_path_var,
                     fg_color=C["card2"], border_color=C["accent"],
                     text_color=C["text"], font=ctk.CTkFont(size=12),
                     width=420, height=34).pack(side="left", padx=12, pady=10)
        ctk.CTkButton(top, text="📁  " + self.t("btn_browse"),
                      fg_color=C["accent"], hover_color=C["accent_h"],
                      height=34, width=110, corner_radius=7,
                      command=self._dir_browse).pack(side="left", padx=4)
        ctk.CTkButton(top, text="🔄  " + self.t("btn_refresh"),
                      fg_color=C["card2"], hover_color=C["accent"],
                      height=34, width=100, corner_radius=7,
                      command=self._dir_refresh).pack(side="left", padx=4)

        # Hızlı kısayollar
        qr = ctk.CTkFrame(outer, fg_color="transparent")
        qr.pack(fill="x", pady=(0,6))
        shortcuts = [
            ("~/İndirilenler", str(Path.home() / "Downloads")),
            ("~/Masaüstü",     str(Path.home() / "Desktop")),
            ("~/.cache",       str(Path.home() / ".cache")),
            ("/tmp",           "/tmp"),
        ]
        for lbl, pth in shortcuts:
            if os.path.exists(pth):
                ctk.CTkButton(qr, text=lbl, height=28,
                              fg_color=C["card2"], hover_color=C["accent"],
                              font=ctk.CTkFont(size=11), corner_radius=6,
                              command=lambda p=pth: (self._dir_path_var.set(p), self._dir_refresh())
                              ).pack(side="left", padx=(0,6))

        # Tablo başlığı
        hdr = ctk.CTkFrame(outer, fg_color=C["card2"], corner_radius=8, height=28)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="  ✓  " + self.t("file_name"),
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=C["sub"], anchor="w").pack(side="left", padx=4)
        for col_txt, w in [(self.t("file_type"), 90), (self.t("dirs_size"), 90)]:
            ctk.CTkLabel(hdr, text=col_txt, width=w,
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=C["sub"]).pack(side="right", padx=8)

        # Scrollable liste — referansı sakla
        scroll = ctk.CTkScrollableFrame(outer, fg_color=C["card"], corner_radius=10)
        scroll.pack(fill="both", expand=True, pady=(2,6))
        self._dir_scroll_ref = scroll

        # Alt butonlar
        bot = ctk.CTkFrame(outer, fg_color="transparent")
        bot.pack(fill="x")
        ctk.CTkButton(bot, text=self.t("select_all"),
                      fg_color=C["card2"], hover_color=C["accent"],
                      height=32, width=120, corner_radius=7,
                      command=self._dir_select_all).pack(side="left", padx=(0,6))
        ctk.CTkButton(bot, text=self.t("deselect_all"),
                      fg_color=C["card2"], hover_color=C["accent"],
                      height=32, width=120, corner_radius=7,
                      command=self._dir_deselect_all).pack(side="left")
        ctk.CTkButton(bot, text="🗑️  " + self.t("btn_delete_selected"),
                      fg_color=C["danger"], hover_color=C["danger_h"],
                      height=32, width=170, corner_radius=7,
                      command=self._dir_delete_selected).pack(side="right")

        self._dir_refresh()

    def _dir_browse(self):
        pth = filedialog.askdirectory(initialdir=self._dir_path_var.get())
        if pth:
            self._dir_path_var.set(pth)
            self._dir_refresh()

    def _dir_refresh(self):
        # Yeni token üret → eski thread'i geçersiz kıl
        self._dir_scan_token += 1
        token = self._dir_scan_token
        self._dir_items      = []
        self._dir_check_vars = []

        scroll = self._dir_scroll_ref
        if scroll is None:
            return
        try:
            for w in scroll.winfo_children():
                w.destroy()
        except Exception:
            return

        self._status(self.t("status_scanning"))
        path = Path(self._dir_path_var.get())
        threading.Thread(
            target=self._dir_load_worker,
            args=(path, token),
            daemon=True
        ).start()

    def _dir_load_worker(self, path: Path, token: int):
        """Arka planda dizin içeriğini listeler. Token değişmişse sonucu atar."""
        items = []
        try:
            entries = sorted(path.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
            for entry in entries:
                if self._dir_scan_token != token:
                    return  # sekme değişti, iptal
                try:
                    if entry.is_symlink():
                        ftype, sz = "🔗 Link", 0
                    elif entry.is_dir():
                        ftype, sz = "📁 Klasör", get_dir_size(entry)
                    else:
                        ftype, sz = "📄 Dosya", entry.stat().st_size
                    items.append((entry, ftype, sz))
                except OSError:
                    pass
        except PermissionError:
            pass

        if self._dir_scan_token != token:
            return  # artık geçersiz

        self.root.after(0, lambda: self._dir_render(items, token))

    def _dir_render(self, items: list, token: int):
        """Ana thread'de widget'ları oluşturur. Token hâlâ geçerliyse devam eder."""
        if self._dir_scan_token != token:
            return
        scroll = self._dir_scroll_ref
        if scroll is None:
            return

        # Widget hâlâ var mı?
        try:
            scroll.winfo_exists()
        except Exception:
            return

        C = self.COLORS
        self._dir_items      = items
        self._dir_check_vars = []

        for entry, ftype, sz in items:
            if self._dir_scan_token != token:
                break
            try:
                var = ctk.BooleanVar(value=False)
                self._dir_check_vars.append(var)
                row = ctk.CTkFrame(scroll, fg_color="transparent", height=30)
                row.pack(fill="x", padx=4, pady=1)
                row.pack_propagate(False)

                name = entry.name
                if len(name) > 44:
                    name = name[:41] + "…"
                ctk.CTkCheckBox(
                    row, text=name, variable=var, width=300,
                    font=ctk.CTkFont(size=12), text_color=C["text"],
                    fg_color=C["accent"], hover_color=C["accent_h"],
                    checkbox_width=18, checkbox_height=18
                ).pack(side="left", padx=6)

                ctk.CTkLabel(row, text=ftype, width=88,
                             font=ctk.CTkFont(size=10), text_color=C["sub"]).pack(side="left")

                col = (C["danger"]  if sz > 200*1024*1024 else
                       C["warning"] if sz > 20*1024*1024  else C["sub"])
                ctk.CTkLabel(row, text=format_size(sz), width=88,
                             font=ctk.CTkFont(size=11), text_color=col).pack(side="left")
            except Exception:
                self._dir_check_vars.append(ctk.BooleanVar(value=False))

        self._status(self.t("scanning_done"))

    def _dir_select_all(self):
        for v in self._dir_check_vars:
            v.set(True)

    def _dir_deselect_all(self):
        for v in self._dir_check_vars:
            v.set(False)

    def _dir_delete_selected(self):
        selected = [
            self._dir_items[i][0]
            for i, v in enumerate(self._dir_check_vars)
            if i < len(self._dir_items) and v.get()
        ]
        if not selected:
            messagebox.showinfo(self.t("confirm_title"), self.t("no_items"))
            return
        preview = "\n".join(p.name for p in selected[:12])
        if len(selected) > 12:
            preview += f"\n… +{len(selected)-12}"
        if not messagebox.askyesno(self.t("confirm_title"),
                                   self.t("confirm_delete") + "\n\n" + preview):
            return
        freed, errors = 0, []
        for p in selected:
            try:
                if p.is_dir() and not p.is_symlink():
                    freed += get_dir_size(p)
                    shutil.rmtree(p)
                else:
                    freed += p.stat().st_size
                    p.unlink()
            except Exception as e:
                errors.append(f"{p.name}: {e}")
        msg = self.t("deleted_ok") + f"\n{self.t('freed_space')}: {format_size(freed)}"
        if errors:
            msg += "\n\nHatalar:\n" + "\n".join(errors[:5])
        messagebox.showinfo(self.t("confirm_title"), msg)
        self._dir_refresh()

    # ═════════════════════════════════════════════════════════════════════════
    # SEKME: TIPS
    # ═════════════════════════════════════════════════════════════════════════

    def _tab_tips(self):
        C = self.COLORS
        frame = ctk.CTkScrollableFrame(self._content, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=26, pady=20)

        ctk.CTkLabel(frame, text="💡  " + self.t("tips_title"),
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=C["text"]).pack(anchor="w")
        ctk.CTkLabel(frame, text=self.t("tips_subtitle"),
                     font=ctk.CTkFont(size=12), text_color=C["sub"]).pack(anchor="w", pady=(2,18))

        tips = SPEED_TIPS.get(self._lang, SPEED_TIPS["tr"])
        for i, (icon, title, desc) in enumerate(tips):
            card = ctk.CTkFrame(frame, fg_color=C["card"], corner_radius=12)
            card.pack(fill="x", pady=5)
            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=16, pady=(12,4))
            ctk.CTkLabel(top, text=f"{i+1:02d}",
                         font=ctk.CTkFont("Monospace", 10), text_color=C["sub"],
                         width=24).pack(side="left")
            ctk.CTkLabel(top, text=icon + "  " + title,
                         font=ctk.CTkFont(size=14, weight="bold"),
                         text_color=C["accent"]).pack(side="left", padx=6)
            lines = desc.count("\n") + 1
            h = max(52, lines * 17 + 22)
            tb = ctk.CTkTextbox(card, height=h, fg_color=C["card2"],
                                text_color=C["text"], font=ctk.CTkFont("Monospace", 12),
                                corner_radius=8, border_width=0)
            tb.pack(fill="x", padx=16, pady=(0,12))
            tb.insert("end", desc)
            tb.configure(state="disabled")


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    App()