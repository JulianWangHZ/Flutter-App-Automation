import time
import pytest
import unittest
import os
from dotenv import dotenv_values
from appium.webdriver import Remote
from appium.options.android import UiAutomator2Options
from appium.options.ios import XCUITestOptions
from utils.initial_setup import get_app_path_for_environment


# TODO: Move the config and options to a separate file
config = dotenv_values(".env")

# In CI environment, read from environment variables if .env is not available
if not config:
    config = os.environ

# Set default values
noReset_bool = config.get('NO_RESET', 'true').lower() == 'true'
platform = config.get('APPIUM_OS', 'ios')
auto_accept_alerts_bool = config.get('AUTO_ACCEPT_ALERTS', 'true').lower() == 'true'

def _is_browserstack():
    """Check if using BrowserStack based on runner setting"""
    # Check environment variable set by conftest.py
    return os.getenv('CURRENT_TEST_RUNNER') == 'browserstack'


def _get_browserstack_app_id():
    """Get BrowserStack app ID based on environment and platform"""
    env = os.getenv('APPIUM_ENV') or config.get('APPIUM_ENV', 'staging')
    env = env.lower()
    
    # Get platform from APPIUM_OS environment variable
    platform = os.getenv('APPIUM_OS', 'ios').lower()
    
    # Normalize platform names
    if platform == 'android':
        platform_prefix = 'ANDROID'
    else:
        platform_prefix = 'IOS'

    
    # Normalize environment name
    if env in ['dev', 'DEV', 'dev_release']:
        env_suffix = 'DEV'
    elif env == 'staging':
        env_suffix = 'STAGING'
    elif env == 'production':
        env_suffix = 'PRODUCTION'
    else:
        env_suffix = 'STAGING'  # Default to staging
    
    # Try platform and environment-specific app ID first
    app_id_key = f'BROWSERSTACK_{platform_prefix}_APP_ID_{env_suffix}'
    app_id = config.get(app_id_key)
    if app_id:
        return app_id
    
    # Fall back to legacy environment-specific app IDs (backwards compatibility)
    legacy_key = f'BROWSERSTACK_APP_ID_{env_suffix}'
    app_id = config.get(legacy_key)
    if app_id:
        return app_id
    
    # Final fallback to generic BROWSERSTACK_APP_ID
    return config.get('BROWSERSTACK_APP_ID')



def _create_browserstack_options(platform='android'):
    """Create BrowserStack configuration options"""
    # Use platform-specific device settings
    if platform == 'ios':
        device_name = config.get('BROWSERSTACK_IOS_DEVICE_NAME', 'iPhone 15 Pro')
        os_version = config.get('BROWSERSTACK_IOS_OS_VERSION', '17')
    elif platform == 'android':
        device_name = config.get('BROWSERSTACK_ANDROID_DEVICE_NAME', 'Google Pixel 8')
        os_version = config.get('BROWSERSTACK_ANDROID_OS_VERSION', '14.0')
    
    return {
        'userName': config.get('BROWSERSTACK_USERNAME'),
        'accessKey': config.get('BROWSERSTACK_ACCESS_KEY'),
        'projectName': config.get('BROWSERSTACK_PROJECT_NAME', 'App E2E Tests'),
        'buildName': config.get('BROWSERSTACK_BUILD_NAME', 'GitHub Actions Build'),
        'sessionName': config.get('BROWSERSTACK_SESSION_NAME', 'E2E Test Session'),
        'deviceName': device_name,
        'osVersion': os_version,
        'interactiveDebugging': True,
        'debug': True,
        'networkLogs': True,
        'appiumLogs': True,
        'deviceLogs': True,
        'video': True
    }


def _configure_android_ci_options(platform='android'):
    """Configure Android options for CI/BrowserStack environment"""
    browserstack_options = _create_browserstack_options(platform)
    
    options = UiAutomator2Options()
    options.platform_name = 'Android'
    options.automation_name = 'UiAutomator2'
    options.app = _get_browserstack_app_id()
    
    # Use Android-specific device configuration
    options.device_name = config.get('BROWSERSTACK_ANDROID_DEVICE_NAME', 'Google Pixel 8')
    options.platform_version = config.get('BROWSERSTACK_ANDROID_OS_VERSION', '14.0')
    
    options.set_capability('autoGrantPermissions', True)
    options.set_capability('autoAcceptAlerts', True)
    options.set_capability('disableWindowAnimation', True)
    options.set_capability('noReset', False)
    options.set_capability('bstack:options', browserstack_options)
    options.set_capability('disableAnimation', False)
    options.set_capability('uiautomator2ServerInstallTimeout', 60000)
    options.set_capability('androidDeviceReadyTimeout', 60)
    options.set_capability('newCommandTimeout', 300)
    options.set_capability('androidInstallTimeout', 90000)
    options.set_capability('adbExecTimeout', 60000)
    return options


def _configure_ios_ci_options(platform='ios'):
    """Configure iOS options for CI/BrowserStack environment"""
    browserstack_options = _create_browserstack_options(platform)
    
    options = XCUITestOptions()
    options.platform_name = 'iOS'
    options.automation_name = 'XCUITest'
    options.device_name = config.get('BROWSERSTACK_IOS_DEVICE_NAME', 'iPhone 15 Pro')
    options.platform_version = config.get('BROWSERSTACK_IOS_OS_VERSION', '17')
    options.app = _get_browserstack_app_id()
    
    options.set_capability('autoAcceptAlerts', True)
    options.set_capability('autoGrantPermissions', True)
    options.set_capability('bstack:options', browserstack_options)
    options.set_capability('simulatorStartupTimeout', 60000)
    options.set_capability('disableAnimation', False)
    options.set_capability('noReset', noReset_bool)
    return options


def _configure_android_local_options():
    """Configure Android options for local environment"""
    options = UiAutomator2Options()
    options.platform_name = 'Android'
    options.automation_name = 'UiAutomator2'
    options.set_capability('language', 'zh')
    options.set_capability('locale', 'TW')
    options.set_capability('app', get_app_path_for_environment('android'))
    options.set_capability('noReset', noReset_bool)
    options.set_capability('autoGrantPermissions', True)
    options.set_capability('autoAcceptAlerts', auto_accept_alerts_bool)
    options.set_capability('skipUnlock', True)
    return options


def _configure_ios_local_options():
    """Configure iOS options for local environment"""
    options = XCUITestOptions()
    options.platform_name = 'iOS'
    options.automation_name = 'XCUITest'
    
    udid = config.get('IOS_UUID') or config.get('IOS_UDID')
    if udid:
        options.udid = udid
        print(f"Using iOS real device UDID: {udid}")
    else:
        device_name = config.get('IOS_DEVICE_NAME', 'iPhone 15 Pro')
        options.device_name = device_name
        print(f"Using iOS simulator: {device_name}")
    
    options.set_capability('language', 'zh')
    options.set_capability('locale', 'TW')
    
    platform_version = config.get('IOS_PLATFORM_VERSION', '17.0')
    options.set_capability('platformVersion', platform_version)
    
    options.set_capability('simulatorStartupTimeout', '90000')
    options.set_capability('app', get_app_path_for_environment('ios'))
    options.set_capability('noReset', noReset_bool)
    options.set_capability('autoAcceptAlerts', auto_accept_alerts_bool)
    options.set_capability('autoGrantPermissions', True)
    return options


def _get_appium_server_url():
    """Get appropriate Appium server URL based on environment"""
    if _is_browserstack():
        return config.get('BROWSERSTACK_HUB_URL', 'https://hub-cloud.browserstack.com/wd/hub')
    return config.get('APPIUM_SERVER_URL', 'http://127.0.0.1:4723')


class AppiumSetup(unittest.TestCase):
    def _get_options(self):
        """Get Appium options based on platform and environment"""
        global config, noReset_bool
        
        # Get platform from environment variable set by conftest.py
        platform = os.getenv('APPIUM_OS', 'ios')
        is_browserstack_env = _is_browserstack()
        print(f"DEBUG: platform={platform}, is_browserstack={is_browserstack_env}")
        
        if is_browserstack_env:
            return self._get_browserstack_options(platform)
        return self._get_local_options(platform)
    
    def _get_browserstack_options(self, platform):
        """Get options for BrowserStack environment"""
        if platform == 'android':
            return _configure_android_ci_options(platform)
        elif platform == 'ios':
            return _configure_ios_ci_options(platform)
        
        raise ValueError(f"Unsupported platform for BrowserStack: {platform}")
    
    def _get_local_options(self, platform):
        """Get options for local environment"""
        if platform == 'android':
            return _configure_android_local_options()
        elif platform == 'ios':
            return _configure_ios_local_options()
        
        raise ValueError(f"Unsupported platform for local: {platform}")
    
    def setUp(self) -> Remote:
        """Set up Appium driver"""
        # Setting global variables
        self.config = config
        self.platform = platform
        self.noReset_bool = noReset_bool

        # Create screenshots directory only in local environment
        self._create_screenshots_directory()

        # Get options and create driver
        options = self._get_options()
        appium_server_url = _get_appium_server_url()
        self.driver = Remote(appium_server_url, options=options)
        self.driver.implicitly_wait(int(config.get('IMPLICIT_WAIT', '25')))

        # Save BrowserStack session ID if using BrowserStack
        self._save_session_id_if_browserstack()

        return self.driver
    
    def _create_screenshots_directory(self):
        """Create screenshots directory for local environment"""
        if not _is_browserstack():
            screenshots_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 
                "screenshots"
            )
            os.makedirs(screenshots_dir, exist_ok=True)
    
    def _save_session_id_if_browserstack(self):
        """Save BrowserStack session ID if using BrowserStack"""
        if _is_browserstack():
            with open('browserstack_session_id.txt', 'w') as f:
                f.write(self.driver.session_id)

    def tearDown(self) -> None:
        """Clean up Appium driver"""
        if self.driver:
            self.driver.quit()
            time.sleep(10)


if __name__ == '__main__':
    unittest.main()