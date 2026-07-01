class Selectors:
    # Login & Auth
    QR_CODE = "canvas[aria-label='Scan me!']"
    LOGGED_IN_INDICATOR = "div[data-testid='chat-list']"
    
    # Chat List
    CHAT_LIST = "div[aria-label='Chat list']"
    CHAT_ITEM = "div[role='listitem']"
    UNREAD_BADGE = "[aria-label*='unread' i], [aria-label*='Unread' i]"
    CHAT_TITLE = "span[title]"
    SEARCH_INPUT = "div[title='Search input textbox']"
    SEARCH_RESULT = "div[role='listitem']"
    
    # Active Chat
    MESSAGE_LIST = "div[role='application']"
    MESSAGE_IN = "div.message-in"
    MESSAGE_OUT = "div.message-out"
    MESSAGE_TEXT = "span.selectable-text.copyable-text"
    MESSAGE_TIME = "span[data-testid='msg-meta']"
    
    # Message Types
    IMAGE_CONTAINER = "div[data-testid='image-thumb']"
    VIDEO_CONTAINER = "div[data-testid='video-thumb']"
    DOCUMENT_CONTAINER = "div[data-testid='audio-download']" # Check this
    VOICE_NOTE = "div[data-testid='audio-play']"
    STICKER = "img[data-testid='sticker']"
    GIF = "div[data-testid='msg-gif']"
    POLL_CONTAINER = "div[data-testid='poll-question']"
    
    # Input Area
    COMPOSE_BOX = "div[title='Type a message']"
    SEND_BUTTON = "span[data-testid='send']"
    ATTACH_BUTTON = "div[title='Attach']"
    
    # Attachments
    ATTACH_IMAGE = "input[accept='image/*,video/mp4,video/3gpp,video/quicktime']"
    ATTACH_DOCUMENT = "input[accept='*']"
    
    # Sender/Author
    AUTHOR_NAME = "span[data-testid='author']"
