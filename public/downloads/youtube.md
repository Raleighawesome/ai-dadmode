---
description: Extract and summarize a YouTube video transcript to an Obsidian note
allowed-tools: ["Bash", "Read", "Write"]
argument-hint: <youtube_url>
---

Extract the transcript from the YouTube video at `$ARGUMENTS`, summarize it, and save as an Obsidian markdown note.

## Instructions

1. Run the transcript extractor script:
   ```bash
   python3 ~/scripts/youtube_transcript_extractor.py "$ARGUMENTS"
   ```

2. If the extraction succeeds, create an Obsidian markdown file with this structure:

   ```markdown
   ---
   title: [Video title if available, otherwise derive from content]
   source: [YouTube URL]
   video_id: [Video ID]
   type: video
   tags:
     - youtube
     - [add 2-3 relevant topic tags based on content]
   created: [Current date in YYYY-MM-DD format]
   ---

   # [Video Title]

   ## Summary
   A concise 2-3 paragraph summary of the main content and purpose of the video.

   ## Key Takeaways
   > [!important]
   > - Bullet points highlighting the most important takeaways
   > - Include insights, arguments, or lessons from the video
   > - Aim for 5-10 key points

   ## Notable Quotes
   > "Quote from the video" (timestamp if available)

   ## Topics Covered
   - List of main topics or themes discussed

   ## Full Transcript
   <details>
   <summary>Click to expand full transcript</summary>

   [Full transcript text here]

   </details>
   ```

3. Save the file to the `youtube` directory at the vault root level (create the directory if it doesn't exist) with a sanitized filename based on the video topic (e.g., `youtube/video-title-summary.md`). Use lowercase, hyphens for spaces, no special characters.

4. Tell the user the filename and location where the note was saved.

5. If the extraction fails, explain the error and suggest alternatives.
