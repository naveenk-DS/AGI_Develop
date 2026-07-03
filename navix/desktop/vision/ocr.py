import pyautogui
from loguru import logger
from navix.desktop.screen.screenshot import take_temp_screenshot
from navix.desktop.vision.screen_reader import ask_llava

async def click_element_by_vision(element: str) -> str:
    try:
        screenshot_path = take_temp_screenshot()
        screen_w, screen_h = pyautogui.size()
        
        # 1. Try PaddleOCR for exact text matching
        try:
            from paddleocr import PaddleOCR
            ocr = PaddleOCR(use_angle_cls=False, lang='en', show_log=False)
            result = ocr.ocr(screenshot_path, cls=False)
            
            if result and result[0]:
                for line in result[0]:
                    box = line[0]
                    text = line[1][0]
                    
                    if element.lower() in text.lower():
                        # box is a list of 4 points: [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
                        center_x = int((box[0][0] + box[1][0]) / 2)
                        center_y = int((box[0][1] + box[2][1]) / 2)
                        pyautogui.click(center_x, center_y)
                        logger.info(f"PaddleOCR Clicked '{text}' at ({center_x}, {center_y})")
                        return f"Found and clicked '{text}' at exact coordinates {center_x}, {center_y} using PaddleOCR"
        except ImportError:
            logger.warning("PaddleOCR not installed. Falling back to LLaVA.")
        except Exception as oe:
            logger.error(f"PaddleOCR error: {oe}")
            
        # 2. Fallback to LLaVA (percentage guessing)
        result = await ask_llava(
            f"Where exactly is the '{element}' on this screen? "
            f"Give me the approximate position as a percentage. "
            f"Example: 'The element is at approximately 30% from left and 20% from top.' "
            f"Only give the position, nothing else.",
            screenshot_path
        )
        
        import re
        left_match = re.search(r"(\d+)%?\s*from\s*left", result, re.IGNORECASE)
        top_match  = re.search(r"(\d+)%?\s*from\s*top", result, re.IGNORECASE)
        
        if left_match and top_match:
            x_pct = int(left_match.group(1)) / 100
            y_pct = int(top_match.group(1)) / 100
            x = int(screen_w * x_pct)
            y = int(screen_h * y_pct)
            pyautogui.click(x, y)
            logger.info(f"LLaVA Clicked '{element}' at ({x}, {y})")
            return f"Clicked {element} at position {x}, {y} using LLaVA fallback"
        else:
            return f"Could not find exact position of {element}. LLaVA said: {result}"
    except Exception as e:
        logger.error(f"Vision click error: {e}")
        return f"Could not click {element}"
