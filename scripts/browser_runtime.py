"""Shared desktop browser identity for hosted-runner requests."""


def desktop_context(browser):
    # Read the installed Chromium identity, retaining its real OS/version.
    # A fixed Windows/old Chrome string would drift from the Linux runtime.
    baseline = browser.new_context()
    try:
        native_user_agent = baseline.new_page().evaluate('navigator.userAgent')
    finally:
        baseline.close()
    user_agent = native_user_agent.replace('HeadlessChrome/', 'Chrome/')
    if 'Chrome/' not in user_agent or 'HeadlessChrome/' in user_agent:
        raise ValueError('Unable to establish desktop Chromium user agent')
    context = browser.new_context(
        locale='en-US', user_agent=user_agent,
        viewport={'width': 1365, 'height': 768}, is_mobile=False, has_touch=False,
    )
    identity = {'native_user_agent': native_user_agent, 'user_agent': user_agent,
                'browser_version': browser.version, 'locale': 'en-US',
                'viewport': {'width': 1365, 'height': 768}, 'profile': 'desktop-linux-chromium'}
    return context, identity
