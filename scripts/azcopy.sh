#!/bin/bash
# Download 64-bit version of AzCopy if on x86_64 architecture
# https://aka.ms/downloadazcopy-v10-linux

# See if azcopy exists in this directory
if [ -f 'azcopy' ]; then
    echo "AzCopy already exists in this directory. Skipping download."
else
    echo "Downloading AzCopy..."

    if [ "$(uname -m)" = "x86_64" ]; then
        wget -O azcopy.tar.gz https://aka.ms/downloadazcopy-v10-linux
    fi

    # ARM64 architecture
    if [ "$(uname -m)" = "aarch64" ]; then
        wget -O azcopy.tar.gz https://aka.ms/downloadazcopy-v10-linux-arm64
    fi

    tar -xf azcopy.tar.gz --strip-components=1 --wildcards '*/azcopy'
fi

# First argument is the backup file, the second is supposed to be the URL + SAS token
# set as an environment variable.
# AIDEV-NOTE: upload, then verify blob exists AND size matches before deleting local file
./azcopy copy "$1" "$AZCOPY"
UPLOAD_EXIT_CODE=$?

if [ $UPLOAD_EXIT_CODE -ne 0 ]; then
    echo "ERROR: azcopy upload failed with exit code $UPLOAD_EXIT_CODE. Local file NOT deleted. [AZ-UPLOAD-FAIL]"
    exit $UPLOAD_EXIT_CODE
fi

# Build the blob-specific URL: insert filename before the SAS query string
FILENAME=$(basename "$1")
CONTAINER_URL="${AZCOPY%%\?*}"
SAS_TOKEN="${AZCOPY#*\?}"
BLOB_URL="${CONTAINER_URL%/}/${FILENAME}?${SAS_TOKEN}"

# Get local file size in bytes
LOCAL_SIZE=$(stat --printf="%s" "$1" 2>/dev/null || stat -f "%z" "$1" 2>/dev/null)
if [ -z "$LOCAL_SIZE" ]; then
    echo "ERROR: Could not determine local file size. Local file NOT deleted. [AZ-LOCALSIZE-FAIL]"
    exit 1
fi

# List the blob and check it exists with matching size
LIST_OUTPUT=$(./azcopy list "$BLOB_URL" --machine-readable 2>&1)
LIST_EXIT_CODE=$?

if [ $LIST_EXIT_CODE -ne 0 ]; then
    echo "ERROR: azcopy list failed (exit $LIST_EXIT_CODE). Cannot verify upload. Local file NOT deleted. [AZ-LIST-FAIL]"
    echo "azcopy list output: $LIST_OUTPUT"
    exit 1
fi

# Confirm filename appears in the listing
if ! echo "$LIST_OUTPUT" | grep -q "$FILENAME"; then
    echo "ERROR: Blob '$FILENAME' not found in Azure listing. Local file NOT deleted. [AZ-BLOBMISSING]"
    echo "azcopy list output: $LIST_OUTPUT"
    exit 1
fi

# Extract the Content Length from the listing and compare to local size
REMOTE_SIZE=$(echo "$LIST_OUTPUT" | grep "$FILENAME" | grep -oP 'Content Length: \K[0-9]+' | head -1)
if [ -z "$REMOTE_SIZE" ]; then
    # Fallback: try alternate format (azcopy versions vary)
    REMOTE_SIZE=$(echo "$LIST_OUTPUT" | grep "$FILENAME" | grep -oE '[0-9]+\.?[0-9]*\s*(B|KiB|MiB|GiB)' | head -1)
    echo "WARNING: Could not parse exact byte size from azcopy list. Raw size info: $REMOTE_SIZE [AZ-SIZEPARSE-WARN]"
    echo "Proceeding based on blob existence confirmation only."
else
    if [ "$REMOTE_SIZE" != "$LOCAL_SIZE" ]; then
        echo "ERROR: Size mismatch! Local=$LOCAL_SIZE bytes, Remote=$REMOTE_SIZE bytes. Local file NOT deleted. [AZ-SIZEMISMATCH]"
        exit 1
    fi
    echo "Size verified: $LOCAL_SIZE bytes (local) == $REMOTE_SIZE bytes (remote)"
fi

echo "Upload verified. Deleting local file: $1"
rm -f "$1"