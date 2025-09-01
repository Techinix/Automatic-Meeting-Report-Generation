from typing import List, Tuple, Any
from app.schemas.langchain import Turn, Conversation
from pyannote.core import Segment
from app.services.celery_worker import c_worker
from app.services.cache import CACHE


def get_text_with_timestamp(segments: List[dict]) -> List[Tuple[Segment, str]]:
    """
    Extracts text with start and end timestamps from segments.

    Args:
        segments (List[dict]): List of segment dictionaries with 'start', 'end', 'text'.

    Returns:
        List[Tuple[Segment, str]]: List of Segment-text tuples.
    """
    timestamp_texts: List[Tuple[Segment, str]] = []
    for item in segments:
        start = item['start']
        end = item['end']
        text = item['text']
        timestamp_texts.append((Segment(start, end), text))
    return timestamp_texts


def get_word_with_timestamp(segments: List[dict]) -> List[Tuple[Segment, str]]:
    """
    Extracts words with start and end timestamps from segments.

    Args:
        segments (List[dict]): List of segment dictionaries with 'words' key.

    Returns:
        List[Tuple[Segment, str]]: List of Segment-word tuples.
    """
    timestamp_texts: List[Tuple[Segment, str]] = []
    for item in segments:
        for word in item["words"]:
            start = word['start']
            end = word['end']
            text = word['word']
            timestamp_texts.append((Segment(start, end), text))
    return timestamp_texts


def add_speaker_info_to_text(
    timestamp_texts: List[Tuple[Segment, str]],
    ann: Any
) -> List[Tuple[Segment, Any, str]]:
    """
    Adds speaker information to timestamped texts using diarization annotations.

    Args:
        timestamp_texts (List[Tuple[Segment, str]]): Timestamped texts.
        ann (Any): Diarization annotation.

    Returns:
        List[Tuple[Segment, Any, str]]: Tuples with segment, speaker, and text.
    """
    spk_text: List[Tuple[Segment, Any, str]] = []
    last_spk = None
    for seg, text in timestamp_texts:
        spk = ann.crop(seg).argmax()
        if spk:
            last_spk = spk
        else:
            spk = last_spk
        spk_text.append((seg, spk, text))
    return spk_text


def merge_cache(text_cache: List[Tuple[Segment, Any, str]]) -> Turn:
    """
    Merges consecutive text segments of the same speaker into a single Turn.

    Args:
        text_cache (List[Tuple[Segment, Any, str]]): List of segment, speaker, text tuples.

    Returns:
        Turn: Merged conversation turn.
    """
    sentence = ''.join([item[-1] for item in text_cache])
    spk = text_cache[0][1]
    start = text_cache[0][0].start
    end = text_cache[-1][0].end
    return Turn(start=start, end=end, speaker=spk, text=sentence)


def merge_sentence(spk_text: List[Tuple[Segment, Any, str]]) -> Conversation:
    """
    Converts speaker-tagged segments into a Conversation object.

    Args:
        spk_text (List[Tuple[Segment, Any, str]]): List of segment, speaker, text tuples.

    Returns:
        Conversation: Aggregated conversation.
    """
    conversation = Conversation(turns=[])
    pre_spk = None
    text_cache: List[Tuple[Segment, Any, str]] = []
    for seg, spk, text in spk_text:
        if spk != pre_spk and pre_spk is not None and len(text_cache) > 0:
            conversation.turns.append(merge_cache(text_cache))
            text_cache = [(seg, spk, text)]
            pre_spk = spk
        else:
            text_cache.append((seg, spk, text))
            pre_spk = spk
    if len(text_cache) > 0:
        conversation.turns.append(merge_cache(text_cache))
    return conversation


def map_chunks(
    transcribe_segments: List[dict],
    diarization_result: Any,
    use_word_timestamps: bool = False
) -> Conversation:
    """
    Maps transcription segments with diarization to create a structured conversation.

    Args:
        transcribe_segments (List[dict]): Transcription segments.
        diarization_result (Any): Diarization annotations.
        use_word_timestamps (bool): Whether to use word-level timestamps.

    Returns:
        Conversation: Structured conversation.
    """
    get_text_func = get_word_with_timestamp if use_word_timestamps else get_text_with_timestamp
    timestamp_texts = get_text_func(transcribe_segments)
    spk_text = add_speaker_info_to_text(timestamp_texts, diarization_result)
    conversation = merge_sentence(spk_text)
    return conversation


@c_worker.task
def create_conversation(keys: List[str], use_word_timestamps: bool = True) -> str:
    """
    Celery task to create a conversation from cached transcription and diarization results.

    Args:
        keys (List[str]): List of cache keys [transcription_key, diarization_key].
        use_word_timestamps (bool): Whether to use word-level timestamps.

    Returns:
        str: Cache key of the created Conversation object.
    """
    segments = CACHE.load(keys[0])
    diarization_result = CACHE.load(keys[1])
    conversation = map_chunks(segments, diarization_result, use_word_timestamps)
    key = CACHE.save(conversation)
    return key
