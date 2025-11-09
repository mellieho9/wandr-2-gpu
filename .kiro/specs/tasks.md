# Implementation Tasks

## Video Processing Pipeline

- [ ] 5. Implement video downloader service

  - [ ] 5.1 Create video downloader with yt-dlp

    - Implement `services/video_downloader.py` with `download()` method
    - Add platform detection for TikTok and Instagram URLs
    - Implement `_download_tiktok()` and `_download_instagram()` using yt-dlp
    - Store downloaded videos in `/tmp` directory with unique filenames
    - _Requirements: 5.2, 5.3_

  - [ ] 5.2 Add retry logic and error handling
    - Implement exponential backoff retry logic (3 attempts)
    - Update Link Database status to "downloading" at start
    - Update status to "transcribing" on success or "failed" on failure
    - _Requirements: 5.1, 5.4, 5.5, 5.6_

- [ ] 6. Implement Whisper transcription service

  - [ ] 6.1 Create Whisper service for audio transcription

    - Implement `services/whisper_service.py` with `transcribe()` method
    - Add `_extract_audio()` method using ffmpeg to extract audio as MP3
    - Call OpenAI Whisper API with audio file
    - Store transcription in video_contents table
    - _Requirements: 6.1, 6.2, 6.3_

  - [ ] 6.2 Add error handling and status updates
    - Handle API rate limits and timeouts with retry logic
    - Update Link Database status to "processing" on success or "failed" on failure
    - _Requirements: 6.4, 6.5_

- [ ] 7. Implement OCR service for text extraction

  - [ ] 7.1 Create OCR service with Google Vision API

    - Implement `services/ocr_service.py` with `extract_text()` method
    - Add `_extract_frames()` method using opencv to extract frames every 2 seconds
    - Implement `_ocr_frame()` method to call Google Vision API for each frame
    - Deduplicate extracted text from multiple frames
    - Store OCR content in video_contents table
    - _Requirements: 7.1, 7.2, 7.3_

  - [ ] 7.2 Add graceful error handling
    - Log OCR errors but continue processing with transcription only
    - Implement 120-second timeout for OCR processing
    - _Requirements: 7.4, 7.5_

- [ ] 8. Implement Gemini summarization service

  - [ ] 8.1 Create Gemini summarizer for schema-specific summaries

    - Implement `services/gemini_summarizer.py` with `summarize()` method
    - Add `_build_prompt()` method to construct prompt with schema, transcription, OCR text, and user prompt
    - Call Gemini 1.5 Pro API requesting JSON output format
    - Implement `_parse_response()` to parse API response into structured data matching Notion schema
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

  - [ ] 8.2 Add validation and error handling
    - Validate parsed response against Notion schema structure
    - Handle API rate limits with exponential backoff
    - Update Link Database status to "saving" on success or "failed" on failure
    - _Requirements: 8.5, 8.6_

- [ ] 9. Implement Notion content writer

  - [ ] 9.1 Create content writer to save to Content Databases

    - Implement method in `clients/notion_client.py` to create pages with structured data
    - Retrieve db_id from notion_schemas table based on tag
    - Map summarized data fields to Notion database properties
    - Include original video_link in the created page
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

  - [ ] 9.2 Add status updates and error handling
    - Update Link Database status to "completed" on successful page creation
    - Update status to "failed" with error message on failure
    - _Requirements: 9.5, 9.6_

- [ ] 10. Implement processing pipeline orchestrator

  - [ ] 10.1 Create pipeline orchestrator

    - Implement `services/processing_pipeline.py` with `process_entry()` method
    - Orchestrate sequential execution: download → transcribe → OCR → summarize → save
    - Inject all service dependencies (downloader, whisper, ocr, summarizer, notion_client)
    - Add `_update_status()` helper method to update Link Database at each stage
    - _Requirements: 5.1, 6.5, 8.6, 9.5_

  - [ ] 10.2 Add cleanup and error handling
    - Implement `_cleanup_temp_files()` method to delete video and audio files
    - Call cleanup after successful completion or failure
    - Handle exceptions at each pipeline stage and update status accordingly
    - _Requirements: 11.1, 11.2_

- [ ] 11. Implement database monitor background worker

  - [ ] 11.1 Create database monitor service

    - Implement `services/database_monitor.py` with `start_monitoring()` method
    - Add `check_for_new_entries()` method to query Link Database for entries with status='pending'
    - Poll every 60 seconds for new entries
    - Validate URL is from TikTok or Instagram
    - Validate tag matches a registered Content Database
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [ ] 11.2 Add queue management
    - Implement `queue_for_processing()` method to add entries to processing_queue table
    - Create background thread or async task to process queued entries
    - Call ProcessingPipeline.process_entry() for each queued entry
    - Update status to "failed" if validation fails
    - _Requirements: 4.5_
