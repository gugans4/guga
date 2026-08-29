# Data dictionary

The generated dataset is synthetic and intended for public portfolio use. It contains one row per event.

| Column | Type | Nullable | Description |
|---|---|---:|---|
| `user_id` | string | no | Anonymous stable user identifier, e.g. `u_000001` |
| `event_name` | string | no | Event from the taxonomy in `docs/metrics.md` |
| `event_timestamp` | datetime UTC | no | Time at which the event occurred |
| `channel` | string | no | First-touch acquisition channel |
| `device_type` | string | no | Device used at signup or journey context |
| `country` | string | no | Coarse country segment |
| `experiment_variant` | string | yes | `control` or `treatment` for exposed users |
| `revenue` | decimal | yes | Revenue attached to a subscription event; null otherwise |

## Journey constraints

The simulator creates a plausible journey in chronological order. A `signup` follows a `landing_view`; `experiment_exposure` follows signup; activation and subscription are downstream events. Not every user completes every stage.

## Privacy and sharing

The dataset contains no names, emails, phone numbers, precise addresses, or production identifiers. Regenerate it locally rather than adding customer or proprietary data.
