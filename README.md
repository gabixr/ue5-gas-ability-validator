# UE5 GAS Ability Validator

A Python editor utility for **Unreal Engine 5** that scans all Gameplay Ability blueprints in your project and flags common **Gameplay Ability System (GAS)** setup issues.

Results are displayed live inside an **Editor Utility Widget** and can be exported as a CSV report.

---

## What It Checks

For every blueprint prefixed `GA_` found under `/Game/`, the validator checks:

| Check | Description |
|---|---|
| Cooldown GE | `CooldownGameplayEffectClass` is assigned |
| Cost GE | `CostGameplayEffectClass` is assigned |
| AbilityTags | Ability has at least one tag |
| CancelAbilitiesWithTag | Tag container is not empty |
| ActivationOwnedTags | Tag container is not empty |
| ActivationBlockedTags | Tag container is not empty |
| GE asset on disk | Assigned Cost/Cooldown GE asset actually exists |

Each ability is reported as `OK`, `WARN` (issues found), or `SKIP` (could not load).

---

## Blueprint Integration

The validator communicates with an **Editor Utility Widget** at the path `/Game/EditorUtilities/EUW_AbilityValidator`. You need to create this widget and expose two Blueprint-callable functions to it.

### 1. Create the Editor Utility Widget

In the Content Browser, right-click and go to **Editor Utilities > Editor Utility Widget**. Name it `EUW_AbilityValidator` and place it under `Content/EditorUtilities/`.

### 2. Add a ScrollBox or ListView for results

In the widget Designer, add a **Vertical Box** or **Scroll Box** to display result rows. This is where each ability result will appear.

### 3. Create the `ClearResults` function

In the widget's **Event Graph**, create a new function named `ClearResults`. Inside it, clear all children from your results container (e.g. call **Remove All Children** on your Vertical Box).

```
Function: ClearResults
  └── Remove All Children (VerticalBox_Results)
```

### 4. Create the `AddResultRow` function

Create a new function named `AddResultRow` with one input parameter:

- **Name:** `Result`  
- **Type:** `String`

Inside the function, create a **Text Block** (or your own styled widget), set its text to the `Result` input, and add it as a child to your results container.

```
Function: AddResultRow (Result: String)
  └── Construct Widget (WBP_ResultRow or Text Block)
  └── Set Text (Result)
  └── Add Child to VerticalBox_Results
```

> Both functions must have **Call In Editor** enabled in their Details panel so Python can invoke them at editor time.

### 5. Open the widget

Run the widget at least once before executing the Python script so that `find_utility_widget_from_blueprint` can find the live instance. Right-click `EUW_AbilityValidator` in the Content Browser and select **Run Editor Utility Widget**.

---

## Running the Validator

With the Python plugin enabled (`Edit > Plugins > Python Editor Script Plugin`), open the **Output Log** and run:

```python
import gas_validator_init
gas_validator_init.ability_validator.run()
```

To run and export a CSV report at the same time:

```python
import gas_validator_init
gas_validator_init.ability_validator.export_csv()
```

The CSV is saved to `Saved/GASValidationReport.csv` in your project folder.

---

## CSV Output Example

| Ability | Status | Issues |
|---|---|---|
| GA_FireBolt | WARN | missing Cooldown GE, missing ActivationBlockedTags |
| GA_Dash | OK | |
| GA_Heal | SKIP | could not load asset |

---

## Adding New Checks

Property checks are driven by two tables at the top of `ability_validator.py`. To add a new check, append a tuple — no changes needed anywhere else.

```python
CHECKS = [
    ("cooldown_gameplay_effect_class", "missing Cooldown GE"),
    ("cost_gameplay_effect_class",     "missing Cost GE"),
    ("your_new_property",              "your warning label"),  # add here
]
```

Tag checks follow the same pattern in `TAG_CHECKS`.

---

## Requirements

- Unreal Engine 5
- Python Editor Script Plugin enabled
