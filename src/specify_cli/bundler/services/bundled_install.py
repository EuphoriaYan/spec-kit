"""Install every bundle in the distribution's packaged catalog."""
from __future__ import annotations

from pathlib import Path

from ..._assets import _locate_core_pack, _repo_root, get_speckit_version
from .. import BundlerError
from ..lib.yamlio import loads_json
from ..models.catalog import load_catalog_payload
from ..models.manifest import BundleManifest
from .adapters import DefaultPrimitiveInstaller
from .installer import InstallResult, install_bundle
from .resolver import resolve_install_plan
from .team_context import initialize_bundled_team_context


def _bundled_catalog_path() -> Path:
    """Locate the distribution catalog in a wheel or source checkout."""
    core = _locate_core_pack()
    if core is not None:
        candidate = core / "bundles" / "catalog.json"
        if candidate.is_file():
            return candidate

    candidate = _repo_root() / "bundles" / "catalog.json"
    if candidate.is_file():
        return candidate

    raise BundlerError(
        "The bundled catalog is missing from this specify-cli installation."
    )


def load_bundled_manifests() -> list[BundleManifest]:
    """Load every manifest listed by the packaged catalog.

    Bundled catalog URLs are package-relative paths. Restricting resolution to
    the catalog directory keeps installation offline and prevents traversal
    outside the trusted distribution assets.
    """
    catalog_path = _bundled_catalog_path()
    payload = loads_json(
        catalog_path.read_text(encoding="utf-8"), origin=str(catalog_path)
    )
    entries = load_catalog_payload(payload)
    catalog_dir = catalog_path.parent.resolve()
    manifests: list[BundleManifest] = []

    for bundle_id in sorted(entries):
        entry = entries[bundle_id]
        relative_path = Path(entry.download_url)
        if relative_path.is_absolute():
            raise BundlerError(
                f"Bundle '{bundle_id}' download_url must be relative to the "
                "bundled catalog."
            )

        manifest_path = (catalog_dir / relative_path).resolve()
        if not manifest_path.is_relative_to(catalog_dir):
            raise BundlerError(
                f"Bundle '{bundle_id}' download_url resolves outside the bundled "
                "catalog directory."
            )
        if not manifest_path.is_file():
            raise BundlerError(
                f"Bundle '{bundle_id}' manifest not found: {manifest_path}"
            )

        manifest = BundleManifest.from_file(manifest_path)
        if manifest.bundle.id != bundle_id:
            raise BundlerError(
                f"Bundled catalog id '{bundle_id}' does not match manifest id "
                f"'{manifest.bundle.id}'."
            )
        if manifest.bundle.version != entry.version:
            raise BundlerError(
                f"Bundled catalog version {entry.version} for '{bundle_id}' does "
                f"not match manifest version {manifest.bundle.version}."
            )
        manifests.append(manifest)

    return manifests


def install_bundled_catalog(
    project_root: Path,
    *,
    active_integration_key: str | None = None,
) -> list[InstallResult]:
    """Install all bundles declared by the packaged catalog, fully offline."""
    from ..lib.project import active_integration

    detected = active_integration_key or active_integration(project_root)
    installer = DefaultPrimitiveInstaller(allow_network=False)
    results: list[InstallResult] = []

    for manifest in load_bundled_manifests():
        plan = resolve_install_plan(
            manifest,
            speckit_version=get_speckit_version(),
            active_integration=detected,
            integration_explicit=bool(active_integration_key),
        )
        results.append(
            install_bundle(
                project_root,
                plan,
                installer,
                manifest=manifest,
                finalize=lambda manifest=manifest: initialize_bundled_team_context(
                    project_root, manifest
                ),
            )
        )

    return results
