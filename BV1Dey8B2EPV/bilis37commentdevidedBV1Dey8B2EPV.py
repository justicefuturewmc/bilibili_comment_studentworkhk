from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import json
import re
import os
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service


class BilibiliCommentSpider:
    def __init__(self, headless=False):
        # 设置Chrome选项
        self.chrome_options = Options()
        self.chrome_options.add_argument(
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

        # 反检测选项
        self.chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.chrome_options.add_experimental_option('useAutomationExtension', False)
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--window-size=1920,1080')

        # 可选：无头模式
        if headless:
            self.chrome_options.add_argument('--headless=new')

        self.driver = None
        self.wait = None
        self.processed_comments = set()  # 用于记录已处理的评论ID
        self.headless = headless  # 保存headless状态

    def init_driver(self):
        """初始化浏览器驱动"""
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=self.chrome_options)
            self.wait = WebDriverWait(self.driver, 15)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => false})")
            print("Chrome driver initialized successfully")
        except Exception as e:
            print(f"Driver init failed: {e}")
            # 降级方案：使用普通webdriver
            self.driver = webdriver.Chrome(options=self.chrome_options)
            self.wait = WebDriverWait(self.driver, 15)

    def login_with_cookies(self):
        """从bili_cookie.txt加载cookie登录"""
        try:
            # 先访问B站主页
            self.driver.get("https://www.bilibili.com")
            time.sleep(3)

            # 检查cookie文件是否存在
            if not os.path.exists('bili_cookie.txt'):
                print("No cookie file found. Running in guest mode.")
                return False

            # 读取cookie文件
            with open('bili_cookie.txt', 'r', encoding='utf-8') as f:
                cookie_str = f.read().strip()

            # 解析cookie字符串
            cookies = []
            for item in cookie_str.split(';'):
                item = item.strip()
                if '=' in item:
                    k, v = item.split('=', 1)
                    cookies.append({
                        'name': k,
                        'value': v,
                        'domain': '.bilibili.com',
                        'path': '/'
                    })

            # 添加cookie到浏览器
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    print(f"添加cookie失败 {cookie.get('name')}: {e}")
                    continue

            # 刷新页面使cookie生效
            self.driver.refresh()
            time.sleep(3)
            print("Cookies loaded successfully")
            return True

        except Exception as e:
            print(f"Cookie登录失败: {e}")
            return False

    def close_driver(self):
        """关闭浏览器"""
        if self.driver:
            # 如果不是无头模式，等待用户确认后再关闭
            if not self.headless:
                user_input = input("\n按回车键关闭浏览器，或输入 'q' 立即退出: ")
                if user_input.lower() == 'q':
                    print("立即关闭浏览器...")
                else:
                    print("浏览器将保持打开，手动关闭或按回车继续...")
                    input()

            self.driver.quit()
            print("浏览器已关闭")

    def get_shadow_element(self, host_element, selector):
        """
        获取Shadow DOM内的元素
        """
        try:
            # 通过JavaScript访问Shadow DOM
            script = """
                var host = arguments[0];
                var selector = arguments[1];
                return host.shadowRoot.querySelector(selector);
            """
            return self.driver.execute_script(script, host_element, selector)
        except Exception as e:
            print(f"获取Shadow DOM元素失败: {e}")
            return None

    def get_shadow_elements(self, host_element, selector):
        """
        获取Shadow DOM内的多个元素
        """
        try:
            script = """
                var host = arguments[0];
                var selector = arguments[1];
                return host.shadowRoot.querySelectorAll(selector);
            """
            return self.driver.execute_script(script, host_element, selector)
        except Exception as e:
            print(f"获取Shadow DOM元素列表失败: {e}")
            return []

    def click_view_more_replies(self, replies_container):
        """
        点击"点击查看"按钮来展开更多回复
        """
        try:
            # 查找"点击查看"按钮
            view_more_button = self.get_shadow_element(replies_container, 'bili-text-button')
            if not view_more_button:
                # 尝试其他选择器
                buttons = self.get_shadow_elements(replies_container, 'bili-text-button')
                for button in buttons:
                    button_text = self.get_shadow_element(button, '.button__label')
                    if button_text and ('点击查看' in button_text.text or '查看' in button_text.text):
                        view_more_button = button
                        break

            if view_more_button:
                # 使用JavaScript点击，避免元素不可点击的问题
                self.driver.execute_script("arguments[0].click();", view_more_button)
                print("点击了'点击查看'按钮")
                time.sleep(3)  # 等待回复加载
                return True
        except Exception as e:
            print(f"点击'点击查看'按钮失败: {e}")
        return False

    def has_next_page_replies(self, replies_container):
        """
        检查回复区域是否有下一页 - 按照total版本简化逻辑
        """
        try:
            pagination_buttons = self.get_shadow_elements(replies_container, 'bili-text-button[data-idx]')
            for button in pagination_buttons:
                button_text = self.get_shadow_element(button, '.button__label')
                if button_text and '下一页' in button_text.text:
                    return True
            return False
        except Exception as e:
            print(f"检查下一页失败: {e}")
            return False

    def click_next_page_replies(self, replies_container):
        """
        点击回复区域的"下一页"按钮 - 按照total版本简化逻辑
        """
        try:
            # 查找分页按钮
            pagination_buttons = self.get_shadow_elements(replies_container, 'bili-text-button[data-idx]')
            for button in pagination_buttons:
                button_text = self.get_shadow_element(button, '.button__label')
                if button_text and '下一页' in button_text.text:
                    self.driver.execute_script("arguments[0].click();", button)
                    print("点击了回复'下一页'按钮")
                    time.sleep(3)
                    return True
        except Exception as e:
            print(f"点击回复下一页失败: {e}")
        return False

    def expand_replies_with_pagination(self, thread, max_pages=500):
        """
        展开回复并处理多页 - 按照total版本逻辑重写
        """
        try:
            replies_container = self.get_shadow_element(thread, 'bili-comment-replies-renderer')
            if not replies_container:
                return []

            # 尝试点击"点击查看"来展开回复
            if self.click_view_more_replies(replies_container):
                time.sleep(2)

            # 收集所有回复
            all_replies = []
            page_count = 0

            while page_count < max_pages:
                # 获取当前页的回复
                reply_elements = self.get_shadow_elements(replies_container, 'bili-comment-reply-renderer')
                current_page_replies = []

                for reply_elem in reply_elements:
                    if len(all_replies) + len(current_page_replies) >= 5000:  # 限制每个评论的回复数量
                        break
                    reply_data = self.extract_reply_data(reply_elem)
                    if reply_data:
                        reply_data['type'] = 'reply'
                        current_page_replies.append(reply_data)

                # 添加到总回复列表
                all_replies.extend(current_page_replies)

                # 检查是否有下一页
                if self.has_next_page_replies(replies_container):
                    print(f"  发现回复第{page_count + 2}页，正在点击...")
                    if self.click_next_page_replies(replies_container):
                        page_count += 1
                        # 等待新页面加载
                        time.sleep(2)
                    else:
                        break
                else:
                    break

            print(f"  共加载了{page_count + 1}页回复，总计{len(all_replies)}条")
            return all_replies

        except Exception as e:
            print(f"展开回复时出错: {e}")
            return []

    def ensure_element_fully_visible(self, element):
        """
        确保元素完全可见在视口中
        """
        try:
            # 使用JavaScript将元素滚动到视口中央
            self.driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center', inline: 'center'});",
                element
            )
            time.sleep(1)

            # 检查元素是否在视口中
            in_viewport = self.driver.execute_script("""
                var elem = arguments[0];
                var rect = elem.getBoundingClientRect();
                return (
                    rect.top >= 0 &&
                    rect.left >= 0 &&
                    rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
                    rect.right <= (window.innerWidth || document.documentElement.clientWidth)
                );
            """, element)

            if not in_viewport:
                # 如果不在视口中，再次滚动
                self.driver.execute_script("window.scrollBy(0, -100);")
                time.sleep(0.5)
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});",
                    element
                )
                time.sleep(1)

        except Exception as e:
            print(f"确保元素可见时出错: {e}")

    def extract_comment_data(self, comment_element):
        """
        从评论元素中提取数据
        """
        try:
            comment_data = {}

            # 获取用户信息
            user_info = self.get_shadow_element(comment_element, 'bili-comment-user-info')
            if user_info:
                # 用户名
                user_name_elem = self.get_shadow_element(user_info, '#user-name a')
                if user_name_elem:
                    comment_data['user_name'] = user_name_elem.text
                    comment_data['user_link'] = user_name_elem.get_attribute('href')

                # 用户等级
                level_elem = self.get_shadow_element(user_info, '#user-level img')
                if level_elem:
                    level_src = level_elem.get_attribute('src')
                    if level_src:
                        # 从等级图标URL中提取等级
                        level_match = re.search(r'level_(\d+)', level_src)
                        if level_match:
                            comment_data['user_level'] = level_match.group(1)

            # 获取评论内容
            rich_text = self.get_shadow_element(comment_element, 'bili-rich-text')
            if rich_text:
                content_elem = self.get_shadow_element(rich_text, '#contents')
                if content_elem:
                    comment_data['content'] = content_elem.text

            # 获取操作按钮信息（点赞数、发布时间等）
            action_buttons = self.get_shadow_element(comment_element, 'bili-comment-action-buttons-renderer')
            if action_buttons:
                # 点赞数
                like_count_elem = self.get_shadow_element(action_buttons, '#like #count')
                if like_count_elem:
                    comment_data['like_count'] = like_count_elem.text

                # 发布时间
                pubdate_elem = self.get_shadow_element(action_buttons, '#pubdate')
                if pubdate_elem:
                    comment_data['publish_time'] = pubdate_elem.text

            # 生成评论的唯一标识
            comment_id = f"{comment_data.get('user_name', '')}_{comment_data.get('content', '')}_{comment_data.get('publish_time', '')}"
            comment_data['comment_id'] = hash(comment_id)

            return comment_data if comment_data else None

        except Exception as e:
            print(f"提取评论数据失败: {e}")
            return None

    def extract_reply_data(self, reply_element):
        """
        从回复元素中提取数据 - 保留devided版本的健壮性
        """
        try:
            reply_data = {}

            # 获取用户信息
            user_info = self.get_shadow_element(reply_element, 'bili-comment-user-info')
            if user_info:
                user_name_elem = self.get_shadow_element(user_info, '#user-name a')
                if user_name_elem:
                    reply_data['user_name'] = user_name_elem.text
                    reply_data['user_link'] = user_name_elem.get_attribute('href')
                else:
                    # 尝试其他选择器
                    user_name_span = self.get_shadow_element(user_info, '#user-name span')
                    if user_name_span:
                        reply_data['user_name'] = user_name_span.text
                        reply_data['user_link'] = ''

            # 获取回复内容
            rich_text = self.get_shadow_element(reply_element, 'bili-rich-text')
            if rich_text:
                content_elem = self.get_shadow_element(rich_text, '#contents')
                if content_elem:
                    reply_data['content'] = content_elem.text
                else:
                    # 尝试其他选择器
                    content_span = self.get_shadow_element(rich_text, 'span')
                    if content_span:
                        reply_data['content'] = content_span.text

            # 获取操作信息
            action_buttons = self.get_shadow_element(reply_element, 'bili-comment-action-buttons-renderer')
            if action_buttons:
                pubdate_elem = self.get_shadow_element(action_buttons, '#pubdate')
                if pubdate_elem:
                    reply_data['publish_time'] = pubdate_elem.text
                else:
                    # 尝试其他选择器
                    pubdate_span = self.get_shadow_element(action_buttons, 'span')
                    if pubdate_span and '前' in pubdate_span.text:  # 常见的时间格式
                        reply_data['publish_time'] = pubdate_span.text

                like_count_elem = self.get_shadow_element(action_buttons, '#like #count')
                if like_count_elem:
                    reply_data['like_count'] = like_count_elem.text
                else:
                    # 尝试其他选择器
                    like_span = self.get_shadow_element(action_buttons, 'span.bili-comment__action--count')
                    if like_span:
                        reply_data['like_count'] = like_span.text

            # 如果没有提取到任何数据，尝试直接获取文本内容
            if not reply_data:
                reply_text = reply_element.text
                if reply_text:
                    reply_data['content'] = reply_text
                    reply_data['user_name'] = '未知用户'
                    reply_data['publish_time'] = '未知时间'
                    reply_data['like_count'] = '0'

            return reply_data if reply_data else None

        except Exception as e:
            print(f"提取回复数据失败: {e}")
            # 尝试获取元素的文本内容作为最后手段
            try:
                reply_text = reply_element.text
                if reply_text:
                    return {
                        'user_name': '未知用户',
                        'content': reply_text,
                        'publish_time': '未知时间',
                        'like_count': '0',
                        'type': 'reply'
                    }
            except:
                pass
            return None

    def smart_scroll(self, comments_container, scroll_count):
        """
        改进的智能滚动策略，确保加载更多评论
        """
        try:
            # 记录当前滚动位置
            current_scroll = self.driver.execute_script("return window.pageYOffset;")

            # 方法1：先向上滚动一点，再向下滚动（模拟人类行为）
            self.driver.execute_script(f"window.scrollTo(0, {current_scroll - 300});")
            time.sleep(1)

            # 方法2：滚动到页面底部
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            print(f"  滚动 #{scroll_count}: 滚动到页面底部")
            time.sleep(3)

            # 方法3：滚动到评论容器
            if comments_container:
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'end'});",
                                           comments_container)
                print(f"  滚动 #{scroll_count}: 滚动到评论容器底部")
                time.sleep(2)

            # 方法4：模拟用户滚动行为 - 滚动到页面特定位置
            current_height = self.driver.execute_script(
                "return document.documentElement.scrollTop || document.body.scrollTop;")
            viewport_height = self.driver.execute_script("return window.innerHeight;")
            scroll_to = current_height + viewport_height * 0.7
            self.driver.execute_script(f"window.scrollTo(0, {scroll_to});")
            print(f"  滚动 #{scroll_count}: 模拟用户滚动")
            time.sleep(2)

            # 检查是否有新内容加载
            new_scroll = self.driver.execute_script("return window.pageYOffset;")
            if new_scroll > current_scroll:
                print(f"  滚动成功，位置变化: {current_scroll} -> {new_scroll}")
            else:
                print(f"  滚动后位置无变化: {new_scroll}")

            return True
        except Exception as e:
            print(f"滚动失败: {e}")
            return False

    def incremental_scroll_and_process(self, comments_container, max_comments=50000, batch_size=20):
        """
        改进的增量滚动并处理评论 - 解决中间评论遗漏问题
        """
        processed_count = 0
        scroll_count = 0
        max_scroll_attempts = 300  # 增加最大滚动尝试次数
        last_comment_count = 0
        no_new_count = 0
        max_no_new = 20  # 增加连续无新评论的最大次数

        # 初始获取评论
        comment_threads = self.get_shadow_elements(comments_container, 'bili-comment-thread-renderer')
        current_count = len(comment_threads)
        print(f"初始评论数量: {current_count}")

        # 添加重试机制
        retry_count = 0
        max_retries = 5

        while (processed_count < max_comments and
               scroll_count < max_scroll_attempts and
               no_new_count < max_no_new and
               retry_count < max_retries):

            # 处理当前可见的评论
            comment_threads = self.get_shadow_elements(comments_container, 'bili-comment-thread-renderer')
            current_count = len(comment_threads)

            print(f"当前可见评论: {current_count}, 已处理: {processed_count}, 滚动次数: {scroll_count}, 无新评论计数: {no_new_count}")

            if current_count > last_comment_count:
                # 处理新加载的评论
                batch_comments = []

                # 从上次处理的位置开始处理新评论
                for i in range(last_comment_count, current_count):
                    if processed_count >= max_comments:
                        break

                    thread = comment_threads[i]
                    try:
                        # 确保评论元素可见
                        self.ensure_element_fully_visible(thread)

                        comment_renderer = self.get_shadow_element(thread, 'bili-comment-renderer')
                        if comment_renderer:
                            comment_data = self.extract_comment_data(comment_renderer)
                            if comment_data and comment_data['comment_id'] not in self.processed_comments:
                                comment_data['type'] = 'main_comment'

                                # 展开回复 - 使用修复后的逻辑
                                comment_data['replies'] = self.expand_replies_with_pagination(thread)

                                # 添加到批次
                                batch_comments.append(comment_data)
                                self.processed_comments.add(comment_data['comment_id'])
                                processed_count += 1

                                # 立即输出单条评论
                                self.output_single_comment(comment_data, processed_count)

                    except Exception as e:
                        print(f"处理评论线程时出错: {e}")
                        continue

                # 批量保存到文件
                if batch_comments:
                    self.save_comments_batch(batch_comments, processed_count)

                last_comment_count = current_count
                no_new_count = 0  # 重置无新评论计数
                retry_count = 0  # 重置重试计数

            else:
                # 没有新评论
                no_new_count += 1
                print(f"无新评论加载，计数: {no_new_count}/{max_no_new}")

                # 如果连续多次没有新评论，尝试更激进的滚动
                if no_new_count % 3 == 0:
                    print("尝试更激进的滚动策略...")
                    self.aggressive_scroll(comments_container, scroll_count)

                # 如果连续5次没有新评论，尝试重新查找评论容器
                if no_new_count % 5 == 0:
                    print("尝试重新定位评论容器...")
                    try:
                        comments_container = self.wait.until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "bili-comments"))
                        )
                        print("评论容器重新定位成功")
                    except Exception as e:
                        print(f"重新定位评论容器失败: {e}")

            # 执行智能滚动
            if processed_count < max_comments and no_new_count < max_no_new:
                scroll_count += 1
                success = self.smart_scroll(comments_container, scroll_count)

                if not success:
                    retry_count += 1
                    print(f"滚动失败，重试计数: {retry_count}/{max_retries}")

                # 偶尔等待更长时间，确保内容加载
                if scroll_count % 5 == 0:
                    print("等待额外时间确保内容加载...")
                    time.sleep(5)

                # 每10次滚动后，尝试滚动到页面顶部再回来，刷新内容
                if scroll_count % 10 == 0:
                    self.refresh_scroll_position(comments_container)

        print(f"增量处理完成，总共处理了 {processed_count} 条评论")
        print(f"最终统计 - 滚动次数: {scroll_count}, 无新评论连续次数: {no_new_count}, 重试次数: {retry_count}")
        return processed_count

    def refresh_scroll_position(self, comments_container):
        """
        刷新滚动位置，解决内容卡住不加载的问题
        """
        try:
            print("执行刷新滚动位置操作...")

            # 先滚动到顶部
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)

            # 再滚动到底部
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

            # 最后滚动到评论区域
            if comments_container:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                    comments_container
                )
                time.sleep(2)

            print("刷新滚动位置完成")
            return True
        except Exception as e:
            print(f"刷新滚动位置失败: {e}")
            return False

    def aggressive_scroll(self, comments_container, scroll_count):
        """
        更激进的滚动策略，用于解决遗漏评论
        """
        try:
            # 方法1：滚动到特定位置
            current_scroll = self.driver.execute_script("return window.pageYOffset;")
            viewport_height = self.driver.execute_script("return window.innerHeight;")

            # 滚动到不同位置
            scroll_positions = [
                current_scroll + viewport_height * 0.3,
                current_scroll + viewport_height * 0.6,
                current_scroll + viewport_height * 0.9
            ]

            for pos in scroll_positions:
                self.driver.execute_script(f"window.scrollTo(0, {pos});")
                time.sleep(1)
                print(f"  激进滚动到位置: {pos}")

            # 方法2：快速滚动到底部再回到中间
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
            time.sleep(2)

            # 方法3：如果评论容器存在，在其内部滚动
            if comments_container:
                self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", comments_container)
                time.sleep(1)

            return True

        except Exception as e:
            print(f"激进滚动失败: {e}")
            return False

    def output_single_comment(self, comment_data, count):
        """立即输出单条评论信息"""
        print(f"\n[{count}] 新评论:")
        print(f"   用户: {comment_data.get('user_name', '未知')}")
        print(f"   内容: {comment_data.get('content', '')[:100]}...")
        print(f"   点赞: {comment_data.get('like_count', '0')}")
        print(f"   时间: {comment_data.get('publish_time', '未知')}")
        print(f"   回复数: {len(comment_data.get('replies', []))}")
        print(f"   等级: {comment_data.get('user_level', '未知')}")

    def save_comments_batch(self, batch_comments, current_count):
        """批量保存评论到文件"""
        try:
            filename = f'bilibili_comments_batch_{current_count}.json'
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(batch_comments, f, ensure_ascii=False, indent=2)
            print(f"✓ 已保存批次到 {filename} (包含 {len(batch_comments)} 条评论)")

            # 同时更新主文件
            self.update_main_file(batch_comments)

        except Exception as e:
            print(f"保存批次文件时出错: {e}")

    def update_main_file(self, new_comments):
        """更新主评论文件"""
        try:
            main_filename = 'bilibili_comments_all.json'
            existing_comments = []

            # 读取现有评论
            if os.path.exists(main_filename):
                with open(main_filename, 'r', encoding='utf-8') as f:
                    existing_comments = json.load(f)

            # 添加新评论
            existing_comments.extend(new_comments)

            # 写回文件
            with open(main_filename, 'w', encoding='utf-8') as f:
                json.dump(existing_comments, f, ensure_ascii=False, indent=2)

            print(f"✓ 主文件已更新，总计 {len(existing_comments)} 条评论")

        except Exception as e:
            print(f"更新主文件时出错: {e}")

    def get_comments(self, video_url, max_comments=50000):
        """
        获取视频评论 - 增量版本
        """
        if not self.driver:
            self.init_driver()

        try:
            # 先登录
            print("正在尝试登录...")
            login_success = self.login_with_cookies()
            if login_success:
                print("登录成功！")
            else:
                print("以游客模式继续...")

            print(f"正在访问视频页面: {video_url}")
            self.driver.get(video_url)

            # 等待页面加载
            time.sleep(5)

            # 等待评论容器加载
            print("等待评论区域加载...")
            comments_container = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "bili-comments"))
            )

            # 初始化主文件
            self.initialize_main_file()

            # 先滚动几次确保初始评论加载
            print("执行初始滚动加载评论...")
            for i in range(3):
                self.smart_scroll(comments_container, i)
                time.sleep(2)

            # 增量滚动和处理评论
            print("开始增量加载评论...")
            total_processed = self.incremental_scroll_and_process(
                comments_container,
                max_comments=max_comments,
                batch_size=20
            )

            return total_processed

        except Exception as e:
            print(f"获取评论时发生错误: {e}")
            return 0

    def initialize_main_file(self):
        """初始化主评论文件"""
        try:
            main_filename = 'bilibili_comments_all.json'
            if not os.path.exists(main_filename):
                with open(main_filename, 'w', encoding='utf-8') as f:
                    json.dump([], f, ensure_ascii=False, indent=2)
                print("主评论文件已初始化")
        except Exception as e:
            print(f"初始化主文件时出错: {e}")

    def print_final_summary(self, total_comments):
        """打印最终统计信息"""
        print(f"\n{'=' * 50}")
        print(f"🎉 爬取完成!")
        print(f"📊 总评论数: {total_comments}")
        print(f"💾 数据已保存到: bilibili_comments_all.json")
        print(f"{'=' * 50}")


def main():
    spider = BilibiliCommentSpider(headless=False)  # 设置为True可在后台运行

    try:
        # B站视频URL
        video_url = "https://www.bilibili.com/video/BV1Dey8B2EPV"  # 请替换为实际视频URL

        # 获取评论
        total_comments = spider.get_comments(
            video_url=video_url,
            max_comments=50000
        )

        # 打印最终统计
        spider.print_final_summary(total_comments)

        print("\n程序执行完毕")

    except Exception as e:
        print(f"主程序运行出错: {e}")
    finally:
        spider.close_driver()


if __name__ == "__main__":
    main()