from src.sources.government import NewsItem


def send_notification(items: list[NewsItem]):
    """Send Windows toast notification with news summary."""
    if not items:
        return

    cats = {}
    for item in items:
        cat = item.category.split(":")[-1].strip()
        cats.setdefault(cat, 0)
        cats[cat] += 1

    summary = " | ".join(f"{cat}: {count}" for cat, count in sorted(cats.items()))

    try:
        from winotify import Notification

        toast = Notification(
            app_id="Bilaspur News Agent",
            title=f"{len(items)} new news items",
            msg=summary[:200],
            duration="short",
        )
        toast.show()
    except ImportError:
        try:
            import subprocess
            ps_script = f"""
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
            $template = [Windows.UI.Notifications.ToastTemplateType]::ToastText02
            $xml = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent($template)
            $texts = $xml.GetElementsByTagName("text")
            $texts.Item(0).AppendChild($xml.CreateTextNode("Bilaspur News Agent")) > $null
            $texts.Item(1).AppendChild($xml.CreateTextNode("{len(items)} new items: {summary[:100]}")) > $null
            $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
            [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Bilaspur News Agent").Show($toast)
            """
            subprocess.run(["powershell", "-Command", ps_script], capture_output=True, timeout=10)
        except Exception:
            pass
