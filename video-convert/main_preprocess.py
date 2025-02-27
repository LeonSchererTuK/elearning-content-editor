from data_providers import data_provider
from data_providers.base import VideoStatus, UnconvertedVideo
import converter
import logging_output as logger
from cleanup import clean_up
from datetime import datetime
from stt import speech_to_text
from convert_ffmpeg import extract_audio
import config
from refinement_openai import refine

def process_video(video: UnconvertedVideo):
    
    # Store the original video file and process it.
    id, filename = converter.store_video_file(video.data, video.file_extension)
    
    audio_file = extract_audio(filename)
    logger.debug("Audio file: " + audio_file)

    transcript = speech_to_text(audio_file)
    logger.debug("Transcript created")

    if config.OPTIMIZE_TRANSCRIPT:
        logger.debug("Optimize Transcript...")
        transcript = refine(transcript, id)
    else:
        logger.debug("Skipping transcript optimization because it is disabled.")

     # convert to json and save to session state
    transcript_obj = transcript.to_dict()
    logger.debug("Transcript optimized")

    # Update the video status to "processed".
    data_provider.update_video_sentences(video, transcript_obj["sentences"])
    data_provider.update_video_status(video, VideoStatus.PREPROCESSED)
    data_provider.reset_errors(video)
    
    logger.debug("Video status updated successfully")

    # Clean up the temporary files.
    clean_up(id)


if __name__ == "__main__":
    # Fetch videos to transcribe.
    unconverted_videos = data_provider.read_unpreprocessed_videos()

    logger.info(f"Found {len(unconverted_videos)} videos to preprocess.")

    # Mark all videos as "preprocessing" so other workers do not take them.
    try:
        for video in unconverted_videos:
            data_provider.update_video_status(video, VideoStatus.PREPROCESSING)
    except Exception as e:
        now = datetime.now()
        message = f"{now.isoformat()} - {str(e)}"

        logger.warning(
            "Failed to update video status to 'processing'. Reverting status to 'unpreprocessed'."
        )
        logger.error("Original error:")
        logger.error(message)

        # Revert the video status to "unpreprocessed".
        for video in unconverted_videos:
            data_provider.update_video_status(video, VideoStatus.UNPREPROCESSED)
            data_provider.add_errors(video, message)

        exit(1)

    # Work on all videos.
    for video in unconverted_videos:
        logger.info(f"Preprocessing video: {video.filename}")

        try:
            process_video(video)
        except Exception as e:
            now = datetime.now()
            message = f"{now.isoformat()} - {str(e)}"

            logger.warning(
                f"Failed to convert video: {video.filename}. Reverting status to 'unprocessed'."
            )
            logger.error("Original error:")
            logger.error(message)

            # Revert the video status to "unprocessed".
            data_provider.update_video_status(video, VideoStatus.UNPROCESSED)

            # Add error message.
            data_provider.add_errors(video, message)
