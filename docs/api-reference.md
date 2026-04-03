# API Reference

Every endpoint requires a valid `Authorization: Bearer <token>` header.

## Health

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Returns service status, database readability, and whether write operations are available |

**Response:**

```json
{
  "status": "healthy",
  "read": true,
  "write": true
}
```

The `status` field is `"healthy"` when the database is readable, or `"degraded"` if it cannot be accessed.

## Todos

| Method | Path | Description |
|---|---|---|
| `GET` | `/todos` | List all incomplete todos |
| `GET` | `/todos/{id}` | Get a specific todo by UUID |
| `POST` | `/todos` | Create a new todo |
| `PUT` | `/todos/{id}` | Update an existing todo |
| `DELETE` | `/todos/{id}` | Complete or cancel a todo (**irreversible**) |

### Query parameters for `GET /todos`

| Parameter | Type | Description |
|---|---|---|
| `project_id` | string | Filter by project UUID |
| `area_id` | string | Filter by area UUID |
| `tag` | string | Filter by tag name |
| `include_checklist` | bool | Include checklist items in the response |

### `POST /todos` — Create

Returns `202 Accepted` with the submitted title. The Things URL scheme does not return the UUID of the created item.

**Request body:**

| Field | Required | Type | Description |
|---|---|---|---|
| `title` | **Yes** | string | Todo title |
| `notes` | No | string | Notes/description |
| `when` | No | string | Schedule: `"today"`, `"tomorrow"`, `"evening"`, `"someday"`, or a date string |
| `deadline` | No | string | Deadline date (YYYY-MM-DD) |
| `tags` | No | string[] | Tag names to apply |
| `checklist_items` | No | string[] | Checklist items to add |
| `list_id` | No | string | Project UUID to add the todo to |
| `list_title` | No | string | Project title to add the todo to |
| `heading` | No | string | Heading name within the project |
| `heading_id` | No | string | Heading UUID within the project |

### `PUT /todos/{id}` — Update

Returns the updated todo if read-back succeeds, or `202 Accepted` if verification times out.

**Request body** (all fields optional):

| Field | Type | Description |
|---|---|---|
| `title` | string | New title |
| `notes` | string | Replace notes |
| `prepend_notes` | string | Prepend to existing notes |
| `append_notes` | string | Append to existing notes |
| `when` | string | Reschedule |
| `deadline` | string | New deadline (YYYY-MM-DD) |
| `tags` | string[] | Replace tags |
| `add_tags` | string[] | Add tags without removing existing ones |
| `checklist_items` | string[] | Replace checklist |
| `prepend_checklist_items` | string[] | Prepend to checklist |
| `append_checklist_items` | string[] | Append to checklist |
| `list_id` | string | Move to project by UUID |
| `list_title` | string | Move to project by title |
| `heading` | string | Move to heading by name |
| `heading_id` | string | Move to heading by UUID |

### `DELETE /todos/{id}` — Complete or cancel

**This action is irreversible.** Things 3 does not support true deletion.

**Request body** (optional):

```json
{"action": "complete"}
```

or

```json
{"action": "cancel"}
```

Defaults to `"complete"` if no body is provided.

## Projects

| Method | Path | Description |
|---|---|---|
| `GET` | `/projects` | List all projects |
| `GET` | `/projects/{id}` | Get a project by UUID |
| `POST` | `/projects` | Create a new project |
| `PUT` | `/projects/{id}` | Update an existing project |
| `DELETE` | `/projects/{id}` | Complete or cancel a project (**irreversible**) |

### `POST /projects` — Create

Returns `202 Accepted`. Request body:

| Field | Required | Type | Description |
|---|---|---|---|
| `title` | **Yes** | string | Project title |
| `notes` | No | string | Notes/description |
| `when` | No | string | Schedule |
| `deadline` | No | string | Deadline date (YYYY-MM-DD) |
| `tags` | No | string[] | Tag names |
| `area_id` | No | string | Area UUID |
| `area_title` | No | string | Area title |
| `todos` | No | string[] | Initial todo titles to create in the project |

### `PUT /projects/{id}` — Update

All fields optional. Same pattern as todo updates (`notes`, `prepend_notes`, `append_notes`, `when`, `deadline`, `tags`, `add_tags`, `area_id`, `area_title`).

### `DELETE /projects/{id}` — Complete or cancel

Same semantics as todo DELETE. **Irreversible.**

## Smart lists

| Method | Path | Description |
|---|---|---|
| `GET` | `/inbox` | Inbox todos |
| `GET` | `/today` | Today's todos |
| `GET` | `/upcoming` | Upcoming scheduled todos |
| `GET` | `/anytime` | Anytime todos |
| `GET` | `/someday` | Someday todos |
| `GET` | `/logbook` | Completed todos |

### Query parameters for `GET /logbook`

| Parameter | Type | Description |
|---|---|---|
| `period` | string | Time period, e.g. `3d` (3 days), `1w` (1 week), `2m` (2 months) |
| `limit` | int | Maximum number of items to return |

## Areas

| Method | Path | Description |
|---|---|---|
| `GET` | `/areas` | List all areas |

### Query parameters

| Parameter | Type | Description |
|---|---|---|
| `include_items` | bool | Include todos and projects within each area |

## Tags

| Method | Path | Description |
|---|---|---|
| `GET` | `/tags` | List all tags |
| `GET` | `/tags/{tag}/items` | Get all items with a specific tag |

### Query parameters for `GET /tags`

| Parameter | Type | Description |
|---|---|---|
| `include_items` | bool | Include tagged items in the response |

## Search

| Method | Path | Description |
|---|---|---|
| `GET` | `/search?q=` | Full-text search across todos |
| `GET` | `/search/advanced` | Filtered search with multiple criteria |

### Query parameters for `GET /search/advanced`

| Parameter | Type | Description |
|---|---|---|
| `status` | enum | `incomplete`, `completed`, or `canceled` |
| `tag` | string | Filter by tag name |
| `area` | string | Filter by area UUID |
| `type` | enum | `to-do`, `project`, or `heading` |
| `start_date` | string | Start date (YYYY-MM-DD) |
| `deadline` | string | Deadline date (YYYY-MM-DD) |
| `last` | string | Time period, e.g. `7d`, `2w`, `1m` |

## Error responses

| Status | Meaning |
|---|---|
| `401 Unauthorized` | Missing or invalid bearer token |
| `404 Not Found` | Todo or project not found by UUID |
| `422 Unprocessable Entity` | Invalid request body |
| `429 Too Many Requests` | Rate limit exceeded (too many failed auth attempts) |
| `500 Internal Server Error` | Write operation failed |
| `503 Service Unavailable` | Write endpoints called without `THINGS_AUTH_TOKEN`, or database not accessible |
