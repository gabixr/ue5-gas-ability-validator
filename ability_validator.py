import unreal
import csv
import os


CHECKS = [
    ("cooldown_gameplay_effect_class", "missing Cooldown GE"),
    ("cost_gameplay_effect_class",     "missing Cost GE"),
]

TAG_CHECKS = [
    ("ability_tags",               "missing AbilityTags"),
    ("cancel_abilities_with_tag",  "missing CancelAbilitiesWithTag"),
    ("activation_owned_tags",      "missing ActivationOwnedTags"),
    ("activation_blocked_tags",    "missing ActivationBlockedTags"),
]


def _has_no_tags(tag_container):
    return tag_container is None or len(tag_container.gameplay_tags) == 0


def _get_widget():
    widget_bp = unreal.load_asset("/Game/EditorUtilities/EUW_AbilityValidator")
    if widget_bp is None:
        return None
    eus = unreal.get_editor_subsystem(unreal.EditorUtilitySubsystem)
    return eus.find_utility_widget_from_blueprint(widget_bp)


def _report(widget, msg):
    print(msg)
    if widget:
        widget.call_method("AddResultRow", (msg,))


def _validate_ability(asset_data):
    asset_path = f"{asset_data.package_name}.{asset_data.asset_name}"
    obj = unreal.load_asset(asset_path)
    if obj is None:
        return "SKIP", "could not load asset"

    generated = obj.generated_class()
    if generated is None:
        return "SKIP", "generated class is None"

    cdo = unreal.get_default_object(generated)
    if cdo is None:
        return "SKIP", "could not get default object"

    issues = []

    for prop, label in CHECKS:
        if not cdo.get_editor_property(prop):
            issues.append(label)

    for prop, label in TAG_CHECKS:
        if _has_no_tags(cdo.get_editor_property(prop)):
            issues.append(label)

    # Warn if Cost GE is set but the asset no longer exists
    cost_ge = cdo.get_editor_property("cost_gameplay_effect_class")
    if cost_ge and not unreal.EditorAssetLibrary.does_asset_exist(cost_ge.get_path_name()):
        issues.append("Cost GE asset missing on disk")

    cooldown_ge = cdo.get_editor_property("cooldown_gameplay_effect_class")
    if cooldown_ge and not unreal.EditorAssetLibrary.does_asset_exist(cooldown_ge.get_path_name()):
        issues.append("Cooldown GE asset missing on disk")

    status = "WARN" if issues else "OK"
    return status, ", ".join(issues)


def run():
    print("GAS Ability Validator Running...")

    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
    bp_filter = unreal.ARFilter(
        class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "Blueprint")],
        recursive_classes=False,
        recursive_paths=True,
        package_paths=["/Game/"]
    )
    abilities = [
        bp for bp in asset_registry.get_assets(bp_filter)
        if str(bp.asset_name).startswith("GA_")
    ]

    widget = _get_widget()
    if widget:
        widget.call_method("ClearResults")

    if not abilities:
        _report(widget, "No abilities found.")
        return []

    _report(widget, f"Found {len(abilities)} abilities")
    results = []

    for ability in abilities:
        status, issues_str = _validate_ability(ability)

        if status == "OK":
            msg = f"[OK]    {ability.asset_name}"
        else:
            msg = f"[{status}] {ability.asset_name}: {issues_str}"

        _report(widget, msg)
        results.append({"Ability": str(ability.asset_name), "Status": status, "Issues": issues_str})

    ok_count   = sum(1 for r in results if r["Status"] == "OK")
    warn_count = sum(1 for r in results if r["Status"] == "WARN")
    skip_count = sum(1 for r in results if r["Status"] == "SKIP")
    _report(widget, f"Done — OK: {ok_count}  WARN: {warn_count}  SKIP: {skip_count}")

    return results


def export_csv():
    results = run()
    if not results:
        return

    saved_path = unreal.Paths.project_saved_dir()
    csv_path = os.path.join(saved_path, "GASValidationReport.csv")

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Ability", "Status", "Issues"])
        writer.writeheader()
        writer.writerows(results)

    print(f"CSV exported to: {csv_path}")