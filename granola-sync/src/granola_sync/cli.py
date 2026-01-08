"""Command-line interface for granola-sync."""
from typing import Optional
import click
import getpass
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt

from .api import GranolaClient
from .export import export_document
from . import config
from .cloud import CloudClient, CloudAPIError, prepare_transcript_for_upload

console = Console()

DEFAULT_OUTPUT_DIR = Path.home() / "Granola" / "transcripts"


@click.group()
@click.version_option()
def main():
    """Sync Granola meeting transcripts to local folders or cloud."""
    pass


@main.command()
@click.option(
    '--output', '-o',
    type=click.Path(path_type=Path),
    default=DEFAULT_OUTPUT_DIR,
    help=f'Output directory for transcripts (default: {DEFAULT_OUTPUT_DIR})'
)
@click.option(
    '--limit', '-l',
    type=int,
    default=None,
    help='Limit number of documents to sync (for testing)'
)
def sync(output: Path, limit: Optional[int]):
    """Sync all Granola transcripts to local folder."""
    console.print(Panel.fit(
        "[bold blue]Granola Transcript Sync[/bold blue]",
        subtitle="Exporting your meeting transcripts"
    ))

    # Create output directory
    output.mkdir(parents=True, exist_ok=True)
    console.print(f"\n[dim]Output directory:[/dim] {output}\n")

    try:
        # Initialize client
        with console.status("[bold green]Connecting to Granola..."):
            client = GranolaClient()
            user_info = client.get_user_info()
            email = user_info.get('email', 'Unknown')

        console.print(f"[green]Connected as:[/green] {email}\n")

        # Fetch documents
        with console.status("[bold green]Fetching document list..."):
            documents = client.get_documents()

        # Filter out deleted
        documents = [d for d in documents if not d.get('deleted_at')]

        if limit:
            documents = documents[:limit]

        console.print(f"[green]Found {len(documents)} documents[/green]\n")

        # Export with progress bar
        exported = 0
        skipped = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Exporting...", total=len(documents))

            for doc in documents:
                doc_id = doc.get('id')
                title = doc.get('title', 'Untitled')[:40]

                progress.update(task, description=f"[cyan]{title}...")

                # Fetch transcript
                transcript = client.get_transcript(doc_id)

                # Export
                try:
                    export_document(doc, transcript, output)
                    exported += 1
                except Exception as e:
                    console.print(f"[yellow]Warning:[/yellow] Failed to export '{title}': {e}")
                    skipped += 1

                progress.advance(task)

        # Summary
        console.print()
        table = Table(title="Sync Complete", show_header=False)
        table.add_row("Exported", f"[green]{exported}[/green]")
        table.add_row("Skipped", f"[yellow]{skipped}[/yellow]")
        table.add_row("Location", str(output))
        console.print(table)

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print("\n[dim]Make sure Granola is installed and you're logged in.[/dim]")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)


@main.command()
def status():
    """Check Granola connection and show account info."""
    try:
        client = GranolaClient()
        user_info = client.get_user_info()

        table = Table(title="Granola Status")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Email", user_info.get('email', 'Unknown'))
        table.add_row("Name", user_info.get('user_metadata', {}).get('name', 'Unknown'))
        table.add_row("Credentials", str(GranolaClient.CREDENTIALS_PATH))

        console.print(table)

    except FileNotFoundError as e:
        console.print(f"[red]Not connected:[/red] {e}")
        raise SystemExit(1)


@main.command()
@click.option(
    '--output', '-o',
    type=click.Path(path_type=Path),
    default=DEFAULT_OUTPUT_DIR,
    help=f'Output directory for transcripts (default: {DEFAULT_OUTPUT_DIR})'
)
def info(output: Path):
    """Show info about synced transcripts."""
    if not output.exists():
        console.print(f"[yellow]No transcripts found at {output}[/yellow]")
        console.print("Run [bold]granola-sync sync[/bold] first.")
        return

    files = list(output.glob("*.md"))
    total_size = sum(f.stat().st_size for f in files)

    table = Table(title="Transcript Info")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Location", str(output))
    table.add_row("Files", str(len(files)))
    table.add_row("Total Size", f"{total_size / 1024 / 1024:.1f} MB")

    if files:
        # Most recent
        most_recent = max(files, key=lambda f: f.stat().st_mtime)
        table.add_row("Most Recent", most_recent.name)

    console.print(table)


# ============ Cloud Commands ============

@main.command()
@click.option('--api-url', '-u', help='API URL (e.g., https://granola-api.yourname.workers.dev)')
@click.option('--email', '-e', help='Your email address')
def login(api_url: Optional[str], email: Optional[str]):
    """Login to cloud API (register if needed)."""
    console.print(Panel.fit(
        "[bold blue]Granola Cloud Login[/bold blue]",
        subtitle="Connect to your team's transcript API"
    ))

    # Get API URL
    if not api_url:
        saved_url = config.get_api_url()
        if saved_url:
            api_url = Prompt.ask("API URL", default=saved_url)
        else:
            api_url = Prompt.ask("API URL (from your admin)")

    # Get email from Granola if not provided
    if not email:
        try:
            granola = GranolaClient()
            user_info = granola.get_user_info()
            default_email = user_info.get('email', '')
            email = Prompt.ask("Email", default=default_email)
        except Exception:
            email = Prompt.ask("Email")

    # Get password
    console.print("[dim]Password is used for ChatGPT OAuth authentication[/dim]")
    password = getpass.getpass("Password: ")
    if not password:
        console.print("[red]Error:[/red] Password is required")
        raise SystemExit(1)

    # Confirm password for new registrations
    password_confirm = getpass.getpass("Confirm password: ")
    if password != password_confirm:
        console.print("[red]Error:[/red] Passwords do not match")
        raise SystemExit(1)

    # Register/login
    with console.status("[bold green]Connecting to API..."):
        try:
            result = CloudClient.register(api_url, email, password)
        except CloudAPIError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise SystemExit(1)

    # Save config
    config.set_api_url(api_url)
    config.set_api_key(result['api_key'])
    config.set_user_info({'email': email, 'user_id': result.get('user_id')})

    console.print()
    table = Table(title="Login Successful", show_header=False)
    table.add_row("API URL", api_url)
    table.add_row("Email", email)
    table.add_row("API Key", result['api_key'][:20] + "...")
    console.print(table)

    console.print("\n[green]You can now run:[/green] granola-sync upload")


@main.command()
@click.option('--limit', '-l', type=int, default=None, help='Limit number of documents')
def upload(limit: Optional[int]):
    """Upload transcripts from Granola to cloud."""
    console.print(Panel.fit(
        "[bold blue]Granola Cloud Upload[/bold blue]",
        subtitle="Syncing your transcripts to the cloud"
    ))

    # Check login
    if not config.is_logged_in():
        console.print("[red]Not logged in.[/red] Run 'granola-sync login' first.")
        raise SystemExit(1)

    try:
        # Initialize clients
        with console.status("[bold green]Connecting..."):
            granola = GranolaClient()
            cloud = CloudClient()
            user_info = granola.get_user_info()
            email = user_info.get('email', 'Unknown')

        console.print(f"[green]Granola:[/green] {email}")
        console.print(f"[green]Cloud API:[/green] {config.get_api_url()}\n")

        # Fetch documents from Granola
        with console.status("[bold green]Fetching documents from Granola..."):
            documents = granola.get_documents()

        documents = [d for d in documents if not d.get('deleted_at')]
        if limit:
            documents = documents[:limit]

        console.print(f"[green]Found {len(documents)} documents[/green]\n")

        # Prepare and upload
        transcripts_to_upload = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Preparing...", total=len(documents))

            for doc in documents:
                doc_id = doc.get('id')
                title = doc.get('title', 'Untitled')[:40]
                progress.update(task, description=f"[cyan]{title}...")

                # Fetch transcript
                transcript = granola.get_transcript(doc_id)

                # Prepare for upload
                prepared = prepare_transcript_for_upload(doc, transcript)
                transcripts_to_upload.append(prepared)

                progress.advance(task)

        # Upload in batches
        console.print("\n[bold]Uploading to cloud...[/bold]")
        batch_size = 50
        total_uploaded = 0
        total_updated = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Uploading...", total=len(transcripts_to_upload))

            for i in range(0, len(transcripts_to_upload), batch_size):
                batch = transcripts_to_upload[i:i + batch_size]
                progress.update(task, description=f"[cyan]Batch {i // batch_size + 1}...")

                result = cloud.upload_transcripts(batch)
                total_uploaded += result.get('uploaded', 0)
                total_updated += result.get('updated', 0)

                progress.advance(task, len(batch))

        # Summary
        console.print()
        table = Table(title="Upload Complete", show_header=False)
        table.add_row("New", f"[green]{total_uploaded}[/green]")
        table.add_row("Updated", f"[yellow]{total_updated}[/yellow]")
        table.add_row("Total in cloud", f"[blue]{total_uploaded + total_updated}[/blue]")
        console.print(table)

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print("\n[dim]Make sure Granola is installed and you're logged in.[/dim]")
        raise SystemExit(1)
    except CloudAPIError as e:
        console.print(f"[red]Cloud API error:[/red] {e}")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)


@main.command('cloud-status')
def cloud_status():
    """Check cloud connection status."""
    table = Table(title="Cloud Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    api_url = config.get_api_url()
    api_key = config.get_api_key()
    user_info = config.get_user_info()

    if not api_url:
        console.print("[yellow]Not configured.[/yellow] Run 'granola-sync login' first.")
        return

    table.add_row("API URL", api_url or "Not set")
    table.add_row("API Key", (api_key[:20] + "...") if api_key else "Not set")
    table.add_row("Email", user_info.get('email', 'Unknown') if user_info else "Unknown")

    # Try to get stats from API
    if api_url and api_key:
        try:
            cloud = CloudClient()
            stats = cloud.get_stats()
            table.add_row("Transcripts in cloud", str(stats.get('totalTranscripts', 0)))
            table.add_row("Last upload", stats.get('lastUpdated', 'Never')[:19] if stats.get('lastUpdated') else 'Never')
            table.add_row("Connection", "[green]OK[/green]")
        except Exception as e:
            table.add_row("Connection", f"[red]Failed: {e}[/red]")

    console.print(table)


@main.command()
def logout():
    """Clear cloud credentials."""
    config.clear_config()
    console.print("[green]Logged out.[/green] Cloud credentials cleared.")


if __name__ == "__main__":
    main()
