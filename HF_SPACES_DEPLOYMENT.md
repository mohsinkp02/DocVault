# Hugging Face Spaces Deployment

This project now runs with one permanent storage backend only:

- `HF`: stores files and simulated folders inside a Hugging Face Hub repository

The current backend is Flask, served from Docker on Hugging Face Spaces. Docker Spaces can run the existing backend and static frontend together.

## Storage model on Hugging Face

DocVault stores each user's files under a user prefix inside the configured repository:

```text
default_user/
  Reports/
    invoice.pdf
    .gitkeep
  Notes/
    ideas.md
```

Key details:

- Folders are simulated using a `.gitkeep` marker committed into each folder path.
- Uploads stream file bytes from the request into the Hugging Face Hub API.
- Folder delete removes every repo path under the folder prefix.
- Folder rename performs a batch copy+delete commit so nested files move together.
- Preview requests are proxied through the backend so PDFs, images, and text can render inline even when the repo is private.

## Required environment variables

Set these in your Hugging Face Space settings:

```bash
SECRET_KEY=replace-me
STORAGE_MODE=HF
HF_TOKEN=hf_xxx_write_token
HF_REPO_ID=your-username/your-docvault-storage
HF_REPO_TYPE=dataset
PORT=7860
```

Notes:

- `HF_TOKEN` must have write access to the target repository.
- `HF_REPO_TYPE=dataset` is recommended for storage-heavy usage.
- Use a private dataset repo unless you explicitly want public file access.

## Deployment steps

1. Create a new Hugging Face Space.
2. Choose `Docker` as the Space SDK.
3. Push this repository to the Space.
4. In the Space settings, add the environment variables listed above.
5. Create the target dataset repository referenced by `HF_REPO_ID`, or allow the app token to create it automatically.
6. Deploy the Space.

After startup:

- the backend serves the static frontend from `/`
- API routes are available under `/api/*`
- file previews are served through `/api/download/<path>`

## Local development against the HF backend

Run the backend with:

```bash
set STORAGE_MODE=HF
set HF_TOKEN=hf_xxx_write_token
set HF_REPO_ID=your-username/your-docvault-storage
set HF_REPO_TYPE=dataset
python server/app.py
```

Then open:

```text
http://127.0.0.1:7860/
```

## Operational behavior

### Create folder

- Validates each folder segment.
- Fails with `FOLDER_EXISTS` if the folder already exists.
- Creates a `.gitkeep` marker at the folder path.

### Upload file

- Uploads directly to the configured HF repository.
- Preserves nested folder structure.
- Auto-renames duplicate filenames using `_1`, `_2`, and so on.

### Delete file or folder

- File delete removes a single repo object.
- Folder delete removes all repo entries under the folder prefix, including the marker file.

### Rename file or folder

- File rename uses a commit copy+delete operation.
- Folder rename moves every file under the folder prefix in one commit.
- Conflicting destination names are rejected with `CONFLICT`.

### Preview support

- Images render inline.
- PDFs render inline in the browser preview.
- Text files are proxied through the backend with inline content headers.
- Private repos work because the backend uses the configured token when fetching content.

## Production notes

- Hugging Face Spaces does not provide persistent local disk for application storage, so this app now fails fast unless `STORAGE_MODE=HF`.
- Keep `HF_TOKEN` in Space secrets, not in repository files.
- Large uploads are still limited by `MAX_CONTENT_LENGTH` in `server/config.py`.
- Repo operations are eventually consistent across commits, so the backend clears its in-memory cache on every write.
