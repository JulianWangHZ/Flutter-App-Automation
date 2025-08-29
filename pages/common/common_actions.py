import time
import os
from typing import Tuple, Union
from appium.webdriver.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions import interaction
from selenium.webdriver.common.actions.pointer_input import PointerInput
from selenium.webdriver.common.actions.action_builder import ActionBuilder


class CommonActions:
    def __init__(self, driver: WebDriver, default_timeout: int = 10):
        """
        Args:
            driver: WebDriver instance
            default_timeout: default timeout (seconds)
        """
        self.driver = driver
        self.wait = WebDriverWait(driver, default_timeout)
        self.default_timeout = default_timeout

    def find_element(self, locator_type: str, locator_value: str, timeout: int = None):
        """
        Use explicit wait to find elements and return
        Add retry mechanism to improve stability

        Args:
            locator_type: Locator type
            locator_value: Locator value
            timeout: Optional timeout, uses default if not specified
        """
        if timeout is None:
            timeout = self.default_timeout

        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                return WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located(
                        (locator_type, locator_value))
                )
            except (TimeoutException, StaleElementReferenceException) as e:
                if attempt == max_attempts - 1:
                    raise TimeoutException(
                        f"Element ({locator_type}={locator_value}) not found after {max_attempts} attempts"
                    ) from e
                time.sleep(1)
                continue
        
        raise TimeoutException(
            f"Element ({locator_type}={locator_value}) not found after {max_attempts} attempts"
        )

    def is_element_visible(self, locator_type: str, locator_value: str, timeout: int = None):

        if timeout is None:
            timeout = self.default_timeout

        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                WebDriverWait(self.driver, timeout).until(
                    EC.visibility_of_element_located(
                        (locator_type, locator_value))
                )
                return True
            except (TimeoutException, StaleElementReferenceException):
                if attempt == max_attempts - 1:
                    return False
                time.sleep(1)
        return False

    def is_element_present(self, locator_type: str, locator_value: str) -> bool:
        try:
            self.driver.find_element(locator_type, locator_value)
            return True
        except NoSuchElementException:
            return False

    def click_element(self, locator_type: str, locator_value: str, timeout: int = None):
        if timeout is None:
            timeout = self.default_timeout

        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable((locator_type, locator_value))
                )
                element.click()
                return
            except (TimeoutException, StaleElementReferenceException) as e:
                if attempt == max_attempts - 1:
                    raise TimeoutException(
                        f"Element ({locator_type}={locator_value}) not clickable after {max_attempts} attempts"
                    ) from e
                time.sleep(1)

    def click_if_exists(self, locator_type: str, locator_value: str) -> bool:
        if self.is_element_visible(locator_type, locator_value):
            self.click_element(locator_type, locator_value)
            return True
        return False

    def send_keys_to_element(self, locator_type: str, locator_value: str, text: str):
        element = self.find_element(locator_type, locator_value)
        element.send_keys(text)
        return element

    def clear_text(self, locator_type: str, locator_value: str):
        element = self.find_element(locator_type, locator_value)
        element.clear()

    def get_element_text(self, locator_type: str, locator_value: str) -> str:
        element = self.find_element(locator_type, locator_value)
        return element.text

    def wait_for_element_visible(self, locator_type: str, locator_value: str, timeout: int = 30):
        """
        Args:
            locator_type: Locator type
            locator_value: Locator value
            timeout: Maximum waiting time (seconds)

        Returns:
            WebElement: If element is visible, return WebElement, otherwise return False

        Raises:
            TimeoutException: If element is not visible within specified time
        """
        try:
            self.driver.implicitly_wait(0)
            wait = WebDriverWait(self.driver, timeout)
            return wait.until(
                EC.visibility_of_element_located((locator_type, locator_value))
            )
        except NoSuchElementException:
            return False
        except TimeoutException:
            actual_timeout = timeout
            raise TimeoutException(
                f"Element ({locator_type}={locator_value}) still not visible after {actual_timeout} seconds"
            )

    def wait_for_element_clickable(self, locator_type: str, locator_value: str) -> bool:
        """
        Wait until specified element is clickable
        """
        try:
            self.wait.until(
                EC.element_to_be_clickable((locator_type, locator_value))
            )
            return True
        except TimeoutException:
            return False

    def verify_element_text(self, locator_type: str, locator_value: str, expected_text: str) -> bool:
        """
        Verify element text
        """
        actual_text = self.get_element_text(locator_type, locator_value)
        return actual_text == expected_text

    def get_platform(self) -> str:
        try:
            platform = os.environ.get('APPIUM_OS', '').lower()
            if platform in ['android', 'ios']:
                return platform
            if hasattr(self.driver, 'desired_capabilities'):
                caps = self.driver.desired_capabilities
                if 'platformName' in caps:
                    platform = caps['platformName'].lower()
                    if platform in ['android', 'ios']:
                        return platform
                
                if 'appium:platformName' in caps:
                    platform = caps['appium:platformName'].lower()
                    if platform in ['android', 'ios']:
                        return platform
                    
            return 'android'
        except Exception:
            return 'android'

    def get_scroll_container_by_platform(self) -> str:
        """
        Get scroll container XPath based on platform
        
        Returns:
            str: XPath for scroll container
        """
        platform = self.get_platform()
        
        if platform == 'ios':
            return "//XCUIElementTypeScrollView | //XCUIElementTypeTable"
        else:
            return "//android.widget.ScrollView | //android.widget.NestedScrollView"

    def scroll_to_element(self, locator_type: str, locator_value: str, scroll_container: str = None, max_swipes: int = 5, timeout: float = 0.5) -> bool:
        """
        Scroll vertically in ScrollView until finding specified element
        Automatically detects platform and uses appropriate scroll container

        Args:
            locator_type: Locator type (e.g. AppiumBy.ID)
            locator_value: Locator value
            scroll_container: ScrollView container xpath, if None will auto-detect by platform
            max_swipes: Maximum swipe count, default is 5
            timeout: Waiting time after each swipe (seconds), default is 0.5 seconds

        Returns:
            bool: If element is found and visible, return True, otherwise return False
        """
        self.driver.implicitly_wait(0)

        try:
            element = self.driver.find_element(locator_type, locator_value)
            if element.is_displayed():
                return True
        except (NoSuchElementException, StaleElementReferenceException):
            pass

        # Get screen size
        screen_width, screen_height = self.get_screen_size()

        # Initialize swipe parameters
        start_x = screen_width // 2
        start_y = int(screen_height * 0.8)  # Start from 80% position
        end_y = int(screen_height * 0.2)    # Scroll to 20% position

        if scroll_container is None:
            scroll_container = self.get_scroll_container_by_platform()

        # Try to find scroll container and adjust swipe range
        try:
            container = self.driver.find_element(By.XPATH, scroll_container)
            container_rect = container.rect

            # Use container size and position
            container_start_y = container_rect['y'] + \
                int(container_rect['height'] * 0.8)
            container_end_y = container_rect['y'] + \
                int(container_rect['height'] * 0.2)
            container_start_x = container_rect['x'] + \
                (container_rect['width'] // 2)

            # Ensure swipe range is valid
            if (container_start_y > container_rect['y'] and
                container_end_y < container_rect['y'] + container_rect['height'] and
                    abs(container_start_y - container_end_y) >= 100):

                start_y = container_start_y
                end_y = container_end_y
                start_x = container_start_x
            else:
                print("Container swipe range is invalid, using screen range")

        except NoSuchElementException:
            print(f"ScrollView container not found with XPath: {scroll_container}, using screen range")

        # Execute swipe
        swipe_count = 0
        last_page_source = self.driver.page_source  # Record page content to check if swipe is effective

        while swipe_count < max_swipes:
            try:

                # Execute swipe
                self.swipe(start_x, start_y, start_x, end_y, duration=1500)
                time.sleep(timeout)

                # Check if element is visible
                try:
                    element = self.driver.find_element(
                        locator_type, locator_value)
                    if element.is_displayed():
                        return True
                except (NoSuchElementException, StaleElementReferenceException):
                    pass

                # Check if swipe is effective (by comparing page content)
                current_page_source = self.driver.page_source
                if current_page_source == last_page_source:
                    print("Page content not changed, swipe may be ineffective")
                    # Try using larger swipe distance
                    start_y = int(screen_height * 0.9)
                    end_y = int(screen_height * 0.1)

                last_page_source = current_page_source
                swipe_count += 1

            except Exception as e:
                print(f"Error during swipe: {str(e)}")
                swipe_count += 1
                continue

        print(f"Swipe {max_swipes} times but still not found target element")
        return False

    def simple_scroll_to_element(self, locator_type: str, locator_value: str, max_swipes: int = 3) -> bool:
        """
        Simple swipe to find element method, using fixed screen ratio for swipe

        Args:
            locator_type: Locator type
            locator_value: Locator value
            max_swipes: Maximum swipe count, default is 3

        Returns:
            bool: If element is found, return True, otherwise return False
        """
        self.driver.implicitly_wait(0)

        # Check if element is already visible
        try:
            element = self.driver.find_element(locator_type, locator_value)
            if element.is_displayed():
                return True
        except (NoSuchElementException, StaleElementReferenceException):
            pass

        # Get screen size
        screen_width, screen_height = self.get_screen_size()

        # Fixed swipe parameters
        start_x = screen_width // 2
        start_y = int(screen_height * 0.8)
        end_y = int(screen_height * 0.2)

        for i in range(max_swipes):
            try:
                print(f"Execute swipe {i + 1} times")

                # Execute swipe
                self.driver.swipe(start_x, start_y, start_x, end_y, 1000)
                time.sleep(1)  # Wait for page to stabilize

                # Check if element is visible
                try:
                    element = self.driver.find_element(
                        locator_type, locator_value)
                    if element.is_displayed():
                        print("Found target element!!")
                        return True
                except (NoSuchElementException, StaleElementReferenceException):
                    pass

            except Exception as e:
                print(f"Error during swipe: {str(e)}")
                continue

        print(f"Swipe {max_swipes} times but still not found target element")
        return False

    def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: int = 800):
        """
        Execute swipe gesture
        """
        self.driver.swipe(start_x, start_y, end_x, end_y, duration)

    def tap(self, x_ratio: float, y_ratio: float):
        """
        Use W3C Actions API to tap on specified screen ratio position

        Args:
        x_ratio (float): x coordinate of screen ratio (0.0 ~ 1.0)
        y_ratio (float): y coordinate of screen ratio (0.0 ~ 1.0)
        Ex.
        self.common_actions.tap(0.5, 0.9)
        """
        size = self.get_screen_size()
        x = int(size[0] * x_ratio)
        y = int(size[1] * y_ratio)
        actions = ActionChains(self.driver)
        pointer = PointerInput(interaction.POINTER_TOUCH, "touch")

        actions.w3c_actions = ActionBuilder(self.driver, mouse=pointer)
        actions.w3c_actions.pointer_action.move_to_location(x, y)
        actions.w3c_actions.pointer_action.pointer_down()
        actions.w3c_actions.pointer_action.pause(0.1)
        actions.w3c_actions.pointer_action.pointer_up()
        actions.perform()

    def hide_keyboard(self):
        self.driver.hide_keyboard()

    def navigate_back(self, times=1):
        for _ in range(times):
            time.sleep(0.5)
            self.driver.back()
            time.sleep(1)

    def get_screen_size(self) -> Tuple[int, int]:
        """
        Get screen size
        """
        size = self.driver.get_window_size()
        return size['width'], size['height']

    def wait_for_element_present(self, locator_type: str, locator_value: str, timeout: int = 30) -> bool:
        """
        Wait for element to appear in DOM and be visible

        Args:
            locator_type: Locator type
            locator_value: Locator value
            timeout: Maximum waiting time (seconds)

        Returns:
            bool: If element appears and is visible, return True, otherwise return False
        """
        try:
            # Temporarily disable implicit wait to avoid conflict with explicit wait
            self.driver.implicitly_wait(0)
            wait = WebDriverWait(self.driver, timeout)
            wait.until(
                EC.visibility_of_element_located((locator_type, locator_value))
            )
            return True
        except TimeoutException:
            return False

    def wait_for_element_disappear(self, locator_type: str, locator_value: str, timeout: int = 30) -> Union[WebElement, bool]:
        """
        Quickly check if element exists and is visible
        If element does not exist, return True immediately

        Args:
            locator_type: Locator type
            locator_value: Locator value
            timeout: Maximum waiting time (seconds)

        Returns:
            Union[WebElement, bool]: If element disappears, return True, otherwise return False

        Raises:
            TimeoutException: If element does not disappear within specified time
        """
        try:
            self.driver.implicitly_wait(0)
            return WebDriverWait(self.driver, timeout).until(EC.invisibility_of_element_located((locator_type, locator_value)))
        except NoSuchElementException:
            return True
        except TimeoutException:
            raise TimeoutException(
                f"Element ({locator_type}={locator_value}) still visible after {timeout} seconds")

    def scroll_to_element_left(self, locator_type: str, locator_value: str, scroll_container: str = "//android.widget.HorizontalScrollView", max_swipes: int = 3, timeout: float = 0.5) -> bool:
        """
        Scroll to element in specified HorizontalScrollView until finding specified element

        Args:
            locator_type: Locator type (e.g. AppiumBy.ID)
            locator_value: Locator value
            scroll_container: HorizontalScrollView container xpath, default is "//android.widget.HorizontalScrollView"
            max_swipes: Maximum swipe count, default is 3
            timeout: Waiting time after each swipe (seconds), default is 0.5 seconds

        Returns:
            bool: If element is found and visible, return True, otherwise return False
        """

        self.driver.implicitly_wait(0)
        try:
            element = self.driver.find_element(locator_type, locator_value)
            if element.is_displayed():
                return True
        except (NoSuchElementException, StaleElementReferenceException):
            pass

        # Get HorizontalScrollView position and size
        try:
            scroll_view = self.driver.find_element(By.XPATH, scroll_container)
            container_rect = scroll_view.rect

            # Get scroll container coordinates and size
            container_x = container_rect['x']
            container_y = container_rect['y']
            container_width = container_rect['width']
            container_height = container_rect['height']

            # Calculate swipe start and end points
            start_x = container_x + int(container_width * 0.8)  # Container right 80% position
            end_x = container_x + int(container_width * 0.2)    # Container left 20% position
            swipe_y = container_y + (container_height // 2)     # Container vertical center position

            for _ in range(max_swipes):
                self.swipe(start_x, swipe_y, end_x, swipe_y)
                time.sleep(timeout)
                try:
                    element = self.driver.find_element(
                        locator_type, locator_value)
                    if element.is_displayed():
                        return True
                except (NoSuchElementException, StaleElementReferenceException):
                    continue

        except NoSuchElementException:
            print("HorizontalScrollView not found")
            return False

        return False

    def get_element_attribute(self, locator_type: str, locator_value: str, attribute: str) -> str:
        """
        Get element attribute value

        Args:
            locator_type: Locator type
            locator_value: Locator value
            attribute: Attribute name

        Returns:
            str: Attribute value
        """
        element = self.find_element(locator_type, locator_value)
        return element.get_attribute(attribute)

    def get_element_location(self, locator_type: str, locator_value: str) -> Tuple[int, int]:
        """
        Get element location

        Args:
            locator_type: Locator type
            locator_value: Locator value

        Returns:
            Tuple[int, int]: Element's x, y coordinates
        """
        element = self.find_element(locator_type, locator_value)
        location = element.location
        return location['x'], location['y']

    def get_element_size(self, locator_type: str, locator_value: str) -> Tuple[int, int]:
        """
        Get element size

        Args:
            locator_type: Locator type
            locator_value: Locator value

        Returns:
            Tuple[int, int]: Element's width and height
        """
        element = self.find_element(locator_type, locator_value)
        size = element.size
        return size['width'], size['height']

    def is_toggle_on(self, locator_type: str, locator_value: str) -> bool:
        """
        Determine toggle state based on checked attribute
        checked="true" means ON, checked="false" means OFF
        """
        try:
            element = self.find_element(locator_type, locator_value)
            checked = element.get_attribute("checked")
            print(f"Toggle checked attribute: {checked}")
            return checked == "true"
        except (NoSuchElementException, TimeoutException):
            return False

    def toggle_switch(self, locator_type: str, locator_value: str, should_be_on: bool = True) -> bool:
        """
        Switch Toggle (Switch) state

        Args:
            locator_type: Locator type
            locator_value: Locator value
            should_be_on: Expected state, True means ON, False means OFF

        Returns:
            bool: If successfully switched to expected state, return True, otherwise return False
        """
        try:
            current_state = self.is_toggle_on(locator_type, locator_value)
            if current_state != should_be_on:
                self.click_element(locator_type, locator_value)
                time.sleep(0.5)
                return self.is_toggle_on(locator_type, locator_value) == should_be_on
            return True
        except (NoSuchElementException, TimeoutException):
            return False

    def _attempt_toggle_switch(self, locator_type: str, locator_value: str, should_be_on: bool) -> bool:
        """
        Try to switch toggle switch

        Args:
            locator_type: Locator type
            locator_value: Locator value
            should_be_on: Expected state

        Returns:
            bool: If successfully switched to expected state, return True, otherwise return False
        """
        element = self.wait.until(
            EC.element_to_be_clickable((locator_type, locator_value))
        )
        element.click()
        time.sleep(1)

        new_state = self.is_toggle_on(locator_type, locator_value)
        print(f"Toggle New State: {'On' if new_state else 'Off'}")

        return new_state == should_be_on

    def _switch_toggle_with_retry(self, locator_type: str, locator_value: str, should_be_on: bool) -> bool:
        """
        Toggle switch with retry mechanism

        Args:
            locator_type: Locator type
            locator_value: Locator value
            should_be_on: Expected state

        Returns:
            bool: If successfully switched to expected state, return True, otherwise return False
        """
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                if self._attempt_toggle_switch(locator_type, locator_value, should_be_on):
                    print(
                        f"Toggle switched to {'On' if should_be_on else 'Off'} state successfully")
                    return True

                if attempt < max_attempts - 1:
                    print(f"Attempt {attempt + 1} failed, trying again...")
                    time.sleep(1)

            except Exception as e:
                print(f"Error during attempt {attempt + 1}: {str(e)}")
                if attempt < max_attempts - 1:
                    time.sleep(1)
                    continue

        print(
            f"Warning: Failed to switch toggle to {'On' if should_be_on else 'Off'} state after {max_attempts} attempts")
        return False

    @staticmethod
    def _handle_toggle_switch_error(locator_type: str, locator_value: str, error: Exception) -> bool:
        """
        Handle toggle switch error

        Args:
            locator_type: Locator type
            locator_value: Locator value
            error: Error

        Returns:
            bool: Always return False
        """
        if isinstance(error, NoSuchElementException):
            print(
                f"Error: Toggle element not found ({locator_type}={locator_value})")
        elif isinstance(error, TimeoutException):
            print(
                f"Error: Waiting for Toggle element timeout ({locator_type}={locator_value})")
        else:
            print(
                f"Error: Unknown error occurred while switching toggle state: {str(error)}")
        return False

    def toggle_switch_state(self, locator_type: str, locator_value: str, should_be_on: bool = True) -> bool:
        """
        Switch Toggle (Switch) state
        - Force switch Toggle to specified state (should_be_on)
        - If current state is different from expected state, switch
        - If current state is the same as expected state, keep it

        Example:
        # Switch to ON state
        common_actions.toggle_switch_state(By.ID, "my_toggle", should_be_on=True)
        # Output:
        # Toggle Current State: Off
        # Toggle New State: On
        # Toggle switched to On state successfully

        # Switch to OFF state
        common_actions.toggle_switch_state(By.ID, "my_toggle", should_be_on=False)
        # Output:
        # Toggle Current State: On
        # Toggle New State: Off
        # Toggle switched to Off state successfully

        Args:
            locator_type: Locator type
            locator_value: Locator value
            should_be_on: Expected state, True means ON, False means OFF

        Returns:
            bool: If successfully switched to expected state, return True, otherwise return False
        """
        try:
            current_state = self.is_toggle_on(locator_type, locator_value)
            print(f"Toggle Current State: {'On' if current_state else 'Off'}")

            if current_state == should_be_on:
                print(
                    f"Toggle is already {'On' if should_be_on else 'Off'}, no need to switch")
                return True

            print(
                f"Switching toggle to {'On' if should_be_on else 'Off'} state")
            return self._switch_toggle_with_retry(locator_type, locator_value, should_be_on)

        except (NoSuchElementException, TimeoutException, Exception) as e:
            return CommonActions._handle_toggle_switch_error(locator_type, locator_value, e)

    def get_element_count(self, locator_type: str, locator_value: str) -> int:
        """
        Find all matching elements and return count
        """
        elements = self.driver.find_elements(locator_type, locator_value)
        return len(elements)

    def wait_for_elements_visible(self, locator_type: str, locator_value: str, timeout: int = 30, min_count: int = 1):
        '''Wait for multiple elements to be visible'''
        try:
            self.driver.implicitly_wait(0)
            wait = WebDriverWait(self.driver, timeout)

            def elements_visible(driver):
                elements = driver.find_elements(locator_type, locator_value)
                visible_elements = [
                    elem for elem in elements if elem.is_displayed()]
                return visible_elements if len(visible_elements) >= min_count else None

            return wait.until(elements_visible)
        except TimeoutException:
            raise TimeoutException(
                f"Expected at least {min_count} elements ({locator_type}={locator_value}) not visible after {timeout} seconds")

    def scroll_to_element_up(self, locator_type: str, locator_value: str, scroll_container: str = "//android.widget.ScrollView", max_swipes: int = 5, timeout: float = 0.5) -> bool:
        """
        Scroll up in ScrollView until finding specified element

        Args:
            locator_type: Locator type (e.g. AppiumBy.ID)
            locator_value: Locator value
            scroll_container: ScrollView container xpath, default is "//android.widget.ScrollView"
            max_swipes: Maximum swipe count, default is 5
            timeout: Waiting time after each swipe (seconds), default is 0.5 seconds

        Returns:
            bool: If element is found and visible, return True, otherwise return False
        """
        self.driver.implicitly_wait(0)

        # Check if element is already visible
        try:
            element = self.driver.find_element(locator_type, locator_value)
            if element.is_displayed():
                return True
        except (NoSuchElementException, StaleElementReferenceException):
            pass

        # Get screen size
        screen_width, screen_height = self.get_screen_size()

        # Initialize swipe parameters (move screen up: finger from top to bottom)
        start_x = screen_width // 2
        start_y = int(screen_height * 0.30)  # Start from 30% position (top)
        end_y = int(screen_height * 0.70)    # Move to 70% position (bottom)

        # Try to find scroll container and adjust swipe range
        try:
            container = self.driver.find_element(By.XPATH, scroll_container)
            container_rect = container.rect

            # Use container size and position (move screen up: finger from top to bottom)
            container_start_y = container_rect['y'] + \
                int(container_rect['height'] * 0.30)
            container_end_y = container_rect['y'] + \
                int(container_rect['height'] * 0.70)
            container_start_x = container_rect['x'] + \
                (container_rect['width'] // 2)

            # Ensure swipe range is valid
            if (container_start_y > container_rect['y'] and
                container_end_y < container_rect['y'] + container_rect['height'] and
                    abs(container_start_y - container_end_y) >= 100):

                start_y = container_start_y
                end_y = container_end_y
                start_x = container_start_x
            else:
                print("Container swipe range is invalid, using screen range")

        except NoSuchElementException:
            print("ScrollView container not found, using screen range")

        # Execute swipe
        swipe_count = 0
        last_page_source = self.driver.page_source  # Record page content to detect if really swiped

        while swipe_count < max_swipes:
            try:

                # Execute upward swipe (use the same parameters as downward swipe)
                self.swipe(start_x, start_y, start_x, end_y, duration=1500)
                time.sleep(timeout)

                # Check if element is visible
                try:
                    element = self.driver.find_element(
                        locator_type, locator_value)
                    if element.is_displayed():
                        return True
                except (NoSuchElementException, StaleElementReferenceException):
                    pass

                # Check if really swiped (by comparing page content)
                current_page_source = self.driver.page_source
                if current_page_source == last_page_source:
                    print("Page content not changed, swipe may be无效")
                    # Try using larger swipe distance (move screen up: finger from top to bottom)
                    start_y = int(screen_height * 0.1)
                    end_y = int(screen_height * 0.9)

                last_page_source = current_page_source
                swipe_count += 1

            except Exception as e:
                print(f"Error during upward swipe: {str(e)}")
                swipe_count += 1
                continue

        print(f"Upward swipe {max_swipes} times but still not found target element")
        return False
