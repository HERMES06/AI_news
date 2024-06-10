from flask import Flask, request
import time

app = Flask(__name__)
static_folder = app.static_folder
api = "__pltKEwoDiASXZhhnRUWmnNVUf9b5cS39S2EA6TxXKZX"

def update_status(task_id, message):
    status_file = f'task_status_v1.txt'
    with open(status_file, 'w', encoding='utf-8') as f:
        f.write(message)

def crawl_news(script_path, gender, politics, age):
    if (script_path == "everytime"):
        import os
        from openai import OpenAI
        from openai import Image
        import requests
        from bs4 import BeautifulSoup
        
        template_image_path = os.path.join(static_folder, 'data', 'AIproject', 'AIproject', 'template_image_2.png')
        bgm_link = os.path.join(static_folder, 'data', 'AIproject', 'AIproject', 'If I Had a Chicken.mp3')

        client = OpenAI(
            # This is the default and can be omitted
            api_key="sk-proj-xw4GZLg51wMd6OiFs3IYT3BlbkFJ9HJApcN7LbYS3HjvDTme",
        )

        category_urls = {
            'economy': 'https://news.naver.com/main/list.naver?mode=LSD&mid=shm&sid1=101',  # 경제
            'politics': 'https://news.naver.com/main/list.naver?mode=LSD&mid=shm&sid1=100',  # 정치
            'society': 'https://news.naver.com/main/list.naver?mode=LSD&mid=shm&sid1=102'   # 사회
        }

        def get_article_content(article_url):
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(article_url, headers=headers)
            
            if response.status_code == 200:
                html = response.text
                soup = BeautifulSoup(html, 'html.parser')
                
                # 기사 제목
                title_tag = soup.find('h2', class_='media_end_head_headline')
                title = title_tag.text.strip() if title_tag else '제목 없음'
                
                # 기사 본문
                content_tag = soup.find('div', id='newsct_article', class_='newsct_article _article_body')
                content = content_tag.text.strip() if content_tag else '본문 없음'
                
                return title, content
            else:
                return None, None

        def get_news_from_category(category, url):
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                html = response.text
                soup = BeautifulSoup(html, 'html.parser')
                
                news_list = soup.find_all('ul', class_='type06_headline')
                articles = news_list[0].find_all('li') if news_list else []
                
                data = []
                
                for article in articles:
                    try:
                        link_tag = article.find('a')
                        link = link_tag['href']
                        title, content = get_article_content(link)
                        if title and content:
                            data.append({'Category': category, 'Title': title, 'Content': content})
                            print(f"제목: {title}\n본문: {content}\n링크: {link}\n")
                    except Exception as e:
                        print("Error parsing article:", e)
                        
                return data
            else:
                print("Failed to retrieve the web page. Status code:", response.status_code)
                return []

        # 카테고리별 기사 크롤링
        all_articles = []
        for category, url in category_urls.items():
            articles = get_news_from_category(category, url)
            all_articles.extend(articles)

        # 크롤링한 데이터 확인
        for article in all_articles:
            print(f"Category: {article['Category']}\nTitle: {article['Title']}\nContent: {article['Content']}\n")

        # OpenAI GPT-4 API를 사용하여 뉴스 요약 및 댓글 생성
        def summarize_and_generate_comments(articles, top_n=5):
            all_contents = "\n\n".join([article['Content'] for article in articles])
            
            prompt = f"""다음 뉴스 기사들을 읽은 후 가장 흥미롭고, 자극적이며, 사회비판적인 중요한 5개의 기사를 선별하여 아래 과정을 수행해.

        다음 뉴스를 핵심 내용으로 요약해줘. 요약문은 아래 내용을 바탕으로 경박한 말투로 작성해.

        1. ~~하다 => 라고함. ~~이다 => 임. ~~했다 => ~~했다고 함. ~~였다 => ~~였던거임. 으로 바꿔서 작성해야 한다. 질문시에는 ~~거야? => ~~거냐?로 바꿔서 작성
        즉, 누군가에게 소식을 듣고 전하듯 말하면서, 말 끝은 ~~함,임으로 끝낸다.
        ex) 트럼프 대통령은 다음 말을 전했다. => 트럼프가 이렇게 말 했다고 함.

        2. 문장 끝에 'ㅋㅋ' 또는 'ㄷㄷ' 을 가끔씩 넣어야 한다.
        ex) 북한이 갑자기 항복을 했다. => 북한이 갑자기 항복을 했다는 거임 ㅋㅋ (재밌거나 어이없는 소식)
        ex) 범인은 사실 A씨가 아닌 B씨 였다. => A가 아니라 B가 범인이였음 ㄷㄷ (놀라울만한 소식)

        3. 뉴스본문을 4 - 5 문장 이내로 간결하게 1, 2의 방법으로 요약한다. 각각의 문장은 15글자 이내로 짧아야 한다. 뉴스 본문임을 표시하기 위해 '본문:'을 먼저 출력하고 요약문을 출력한다.

        4. 바로 다음줄 부터는 뉴스 내용에 대해 일반적인 {politics} 정치 성향을 가진 {age[0]}0대 {gender}성이 달만한 댓글을 출력한다. 간결하고 짧은 한문장으로 구성되며, 댓글의 수는 4개로 고정한다. 아래 예시 형식을 참고한다.

        댓글은 되도록 경박한, 비꼬는 말투를 사용한다. 또한 비판적으로 사고해야 한다. 그러나 거짓된 사실이 들어가서는 안된다. 간결하고 짧은 말투를 사용한다. 댓글 앞에는 항상 '댓글:'을 먼저 출력하고 댓글을 출력한다.

        ex1) 감정표현) 재미있을 때 : ㅋㅋㅋㅋㅋㅋ, 놀라울 때 : ㄷㄷㄷ 이거 진짜임?, 화나는 내용일 때 : 아 개빡치네...
        ex2) 뉴스 내용 되묻기(상세 설명 요청하기)) : ex) 왜 트럼프는 저렇게 말한거임?, ex) 그래서 이제 김모씨는 어떻게 되는거냐?
        (ex2)의 댓글의 바로 다음 댓글은 그에 대한 대답으로 고정한다.두 문장 까지 사용 가능하다) ex) 징역 15년 형 받고 감옥 체험중
        ex3) 뉴스에 공감 요청하기 : 형식 :  아 ㅋㅋ (공감을 유도하고자 하는 내용) + 일 것같으면 개추 ㅋㅋ 의 형식으로 사용. : ex) 아 ㅋㅋ 언젠간 이렇게 될 줄 알았으면 개추 ㅋㅋ, 아 ㅋㅋ 우리나라 경제 좆된거 같으면 개추 ㅋㅋ, 아 ㅋㅋ 이새끼 너무 추한거같으면 개추 ㅋㅋ
        (ex3)의 댓글의 바로 다음 댓글은 개추 ㅋㅋ 으로 고정한다.)
        ex4) 핵심 찌르기 : 뉴스의 핵심을 간파하고 내용을 설명한다 : 형식 : 팩트) ~~~이다. ex) 팩트) 이러다가 한국 좆되는거 순식간이다

        5. 뉴스 마다 구분을 위해 하나의 뉴스를 정리한 이후에는 -----을 출력

        6. 여기서 언급한 내용 이외의 쓸데없는 코멘트, 주석, 제목 등등 다양한 부가적인 것들은 달지마

        <예시 (요약문 5개 중 하나)>

        본문: 우리나라 이번에 미국한테 사기당한 듯. 북한이 미사일 쏘는데 미국이 자기만 알고 우리한테 안알려줌. 이거 완전 큰일 났다는 신호임 ㅋㅋ.

        댓글:아 ㅋㅋㅋㅋ 이제 우리나라 떠나야 할 것 같으면 개추 ㅋㅋ
        댓글:개추 ㅋㅋㅋㅋ
        댓글:이건 왜 이렇게 된거냐?
        댓글:트럼프가 공식 발표해서 이렇게 됨

        -----

        \n\n{all_contents}"""

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", 
                    "content": prompt}
                ],
                
            )
            if response.choices and response.choices[0].message:
                return response.choices[0].message.content.strip() 
            else:
                return "No completion found."
            
        # API 키 설정 및 요약문과 댓글 생성
        selected_summaries = summarize_and_generate_comments(all_articles)
        print(selected_summaries)


        import openai
        from gtts import gTTS
        from moviepy.editor import concatenate_audioclips, concatenate_videoclips, CompositeVideoClip, TextClip, ImageClip, AudioFileClip
        import os
        from pydub import AudioSegment


        # GPT로 생성한 요약 및 댓글 분리
        def extract_texts_and_comments(selected_summaries):
            lines = selected_summaries.split('\n')
            
            texts = []
            comments = []
            current_text = []
            current_comment = []
            reading_text = True

            for line in lines:
                if line.startswith("-----"):  # 뉴스 항목 구분
                    if current_text:
                        texts.append("\n".join(current_text)) #texts list : [i - 1] : i번째 뉴스 텍스트
                        current_text = []
                    if current_comment:
                        comments.append("\n".join(current_comment)) #comments list : [i - 1] : i번째 뉴스 댓글
                        current_comment = []
                    reading_text = True  # 새로운 뉴스 항목 시작
                elif line.startswith("본문:"):
                    reading_text = True
                    current_text.append(line[len("본문:"):].strip())
                elif line.startswith("댓글:"):
                    reading_text = False
                    current_comment.append(line[len("댓글:"):].strip())
                elif reading_text:
                    current_text.append(line.strip())
                else:
                    current_comment.append(line.strip())

            if current_text:
                texts.append("\n".join(current_text))
            if current_comment:
                comments.append("\n".join(current_comment))

            return texts, comments

        # DALL-E를 사용하여 이미지 생성
        def generate_images_for_news(texts, api_key):
            openai.api_key = api_key
            image_urls = []
            
            for text in texts:
                strT = f"{text}\n 이 텍스트와 어울리는 이미지를 DALL-E의 보안 규정에 맞게 잘 생성할 수 있도록 텍스트를 변환해서 그 텍스트만 출력해줘. 다시한번 말하지만 DALL-E가 거부하지 않고 생성할만한 텍스트야."
                response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", 
                    "content": strT}
                ],
                )
                res = response.choices[0].message.content.strip()
                response = client.images.generate(
                    model = "dall-e-3",
                    prompt=res,
                    n=1,
                    size="1024x1024",
                    quality="standard",
                )
                image_urls.append(response.data[0].url)
            return image_urls


        import requests
        from time import sleep

        def typecast_tts(text, actor_id, API_TOKEN):
            HEADERS = {'Authorization': f'Bearer {API_TOKEN}'}
            # 음성 합성 요청
            response = requests.post('https://typecast.ai/api/speak', headers=HEADERS, json={
                'text': text,
                'lang': 'auto',  # 언어 설정, 'ko'로 설정 가능
                'actor_id': actor_id,
                "tempo": 1.3,
                'xapi_hd': True,
                'model_version': 'latest'
            })
            speak_url = response.json()['result']['speak_v2_url']

            # 음성 합성 결과 폴링
            for _ in range(120):  # 최대 2분 대기
                response = requests.get(speak_url, headers=HEADERS)
                ret = response.json()['result']
                if ret['status'] == 'done':
                    # 음성 파일 다운로드
                    audio_response = requests.get(ret['audio_download_url'])
                    filename = f"tts_{hash(text)}.mp3"
                    with open(filename, 'wb') as f:
                        f.write(audio_response.content)
                    return filename
                sleep(1)
            return None

        import openai
        from gtts import gTTS
        from moviepy.editor import concatenate_audioclips, concatenate_videoclips, CompositeVideoClip,CompositeAudioClip, TextClip, ImageClip, AudioFileClip, VideoFileClip
        import os
        from pydub import AudioSegment
        from datetime import date

        def tts_and_duration_typecast(text, actor_id, API_TOKEN, lang='ko'):
            if not text.strip():
                return None, 0
            filename = typecast_tts(text, actor_id, API_TOKEN)
            audio_clip = AudioFileClip(filename)
            return audio_clip, audio_clip.duration



        def create_video_for_news(text, comment, image_url, template_image_path, output_filename):
            target_size = (1080, 1920)  # 세로 HD 포맷
            template_image = ImageClip(template_image_path).resize(newsize=target_size)
            
            desired_image_size = (600, 600)  # 원하는 이미지 크기 설정
            main_image = ImageClip(image_url).resize(newsize=desired_image_size).set_position((240, 400))

            sentences = text.split('. ')
            comments = comment.split('\n')
            audio_list = []
            duration_list = []

            actor_id = "6059dad0b83880769a50502f"

            # TTS 오디오 생성
            for content in sentences + comments:
                audio_clip, duration = tts_and_duration_typecast(content, actor_id, api)
                audio_list.append(audio_clip)
                duration_list.append(duration)

            total_duration = sum(duration_list)
            current_time = 0

            
            all_audios = []
            all_video_clips = [template_image.set_duration(total_duration), main_image.set_duration(total_duration)] 

            # 본문 자막 생성
            y_position = 1020  # 본문 자막의 시작 위치
            for idx, sentence in enumerate(sentences):
                if audio_list[idx]:
                    all_audios.append(audio_list[idx])
                    text_clip = TextClip(sentence, fontsize=35, color='black', font='나눔고딕-Bold')
                    text_clip = text_clip.set_position(('center', y_position)).set_start(current_time).set_duration(total_duration - current_time)
                    all_video_clips.append(text_clip)
                    y_position += 80  # 다음 문장의 위치 조정
                current_time += duration_list[idx]

            # 댓글 자막 생성
            y_position = 1467  # 댓글 자막의 시작 위치
            for comment_idx, comment in enumerate(comments, start=len(sentences)):
                if audio_list[comment_idx]:
                    all_audios.append(audio_list[comment_idx])
                    comment_clip = TextClip('└  '+comment, fontsize=33, color='black', font='나눔고딕-Bold')
                    comment_clip = comment_clip.set_position((170, y_position)).set_start(current_time).set_duration(total_duration - current_time)
                    all_video_clips.append(comment_clip)
                    y_position += 104 # 다음 댓글의 위치 조정
                current_time += duration_list[comment_idx]


            today = str(date.today())
            Title = today[5:7] + '월' + today[8:10] + '일' + '자 뉴스 벌써 뜸'

            date_clip = TextClip(Title, fontsize=55, color='black', font='나눔고딕-Bold')
            date_clip = date_clip.set_position((215, 170)).set_duration(total_duration)

            all_video_clips.append(date_clip)

            # 비디오 및 오디오 결합
            final_video = CompositeVideoClip(all_video_clips).set_duration(total_duration)
            final_audio = concatenate_audioclips(all_audios)

            # 최종 비디오 파일 생성
            #final_clip = final_video.set_audio(final_audio)

            return total_duration, final_video, final_audio

            #final_clip.write_videofile(output_filename, codec='mpeg4', fps=24)


        # API 키 설정 및 이미지 생성
        api_key = 'sk-proj-xw4GZLg51wMd6OiFs3IYT3BlbkFJ9HJApcN7LbYS3HjvDTme'
        texts, comments = extract_texts_and_comments(selected_summaries)
        image_urls = generate_images_for_news(texts, api_key)




        # 템플릿 이미지 경로

        Audio = []
        Video = []
        totaltime = 0

        # 각각의 뉴스를 위한 비디오 생성 및 저장
        for i, (text, comment, image_url) in enumerate(zip(texts, comments, image_urls)):
            print(text + '\n' +  comment)
            output_filename = f"news_video_{i+1}.avi"
            D, Vid, Aud = create_video_for_news(text, comment, image_url, template_image_path, output_filename)
            totaltime += D
            Video.append(Vid), Audio.append(Aud)


        Video_output = concatenate_videoclips(Video)
        bgm = AudioFileClip(bgm_link).set_duration(totaltime).volumex(0.5)
        Audio_output = CompositeAudioClip([concatenate_audioclips(Audio), bgm]).set_duration(totaltime)

        final_clip = Video_output.set_audio(Audio_output)
        final_clip.write_videofile(f'newsGenerator_v1.avi', codec='mpeg4', fps=24) 
        
    elif (script_path == "dcinside"):
        update_status('v1', "뉴스 크롤링 시작")
        import os
        from openai import OpenAI
        from openai import Image
        import requests
        from bs4 import BeautifulSoup

        template_image_path = os.path.join(static_folder, 'data', 'AIproject', 'AIproject', 'template.png')
        bgm_link = os.path.join(static_folder, 'data', 'AIproject', 'AIproject', 'If I Had a Chicken.mp3')

        client = OpenAI(
            # This is the default and can be omitted
            api_key="sk-proj-xw4GZLg51wMd6OiFs3IYT3BlbkFJ9HJApcN7LbYS3HjvDTme",
        )

        category_urls = {
            'economy': 'https://news.naver.com/main/list.naver?mode=LSD&mid=shm&sid1=101',  # 경제
            'politics': 'https://news.naver.com/main/list.naver?mode=LSD&mid=shm&sid1=100',  # 정치
            'society': 'https://news.naver.com/main/list.naver?mode=LSD&mid=shm&sid1=102'   # 사회
        }

        def get_article_content(article_url):
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(article_url, headers=headers)
            
            if response.status_code == 200:
                html = response.text
                soup = BeautifulSoup(html, 'html.parser')
                
                # 기사 제목
                title_tag = soup.find('h2', class_='media_end_head_headline')
                title = title_tag.text.strip() if title_tag else '제목 없음'
                
                # 기사 본문
                content_tag = soup.find('div', id='newsct_article', class_='newsct_article _article_body')
                content = content_tag.text.strip() if content_tag else '본문 없음'
                
                return title, content
            else:
                return None, None

        def get_news_from_category(category, url):
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                html = response.text
                soup = BeautifulSoup(html, 'html.parser')
                
                news_list = soup.find_all('ul', class_='type06_headline')
                articles = news_list[0].find_all('li') if news_list else []
                
                data = []
                
                for article in articles:
                    try:
                        link_tag = article.find('a')
                        link = link_tag['href']
                        title, content = get_article_content(link)
                        if title and content:
                            data.append({'Category': category, 'Title': title, 'Content': content})
                            print(f"제목: {title}\n본문: {content}\n링크: {link}\n")
                    except Exception as e:
                        print("Error parsing article:", e)
                        
                return data
            else:
                print("Failed to retrieve the web page. Status code:", response.status_code)
                return []

        # 카테고리별 기사 크롤링
        all_articles = []
        for category, url in category_urls.items():
            articles = get_news_from_category(category, url)
            all_articles.extend(articles)

        # 크롤링한 데이터 확인
        for article in all_articles:
            print(f"Category: {article['Category']}\nTitle: {article['Title']}\nContent: {article['Content']}\n")

        # OpenAI GPT-4 API를 사용하여 뉴스 요약 및 댓글 생성
        def summarize_and_generate_comments(articles, top_n=5):
            all_contents = "\n\n".join([article['Content'] for article in articles])
            
            prompt = f"""다음 뉴스 기사들을 읽은 후 가장 흥미롭고, 자극적이며, 사회비판적인 중요한 5개의 기사를 선별하여 아래 과정을 수행해.

        다음 뉴스를 핵심 내용으로 요약해줘. 요약문은 아래 내용을 바탕으로 경박한 말투로 작성해.

        1. ~~하다 => 라고함. ~~이다 => 임. ~~했다 => ~~했다고 함 등으로 바꿔서 작성해야 한다. 질문시에는 ~~거야? => ~~거냐?로 바꿔서 작성
        즉, 누군가에게 소식을 듣고 전하듯 말하면서, 말 끝은 ~~함,임으로 끝낸다.
        ex) 트럼프 대통령은 다음 말을 전했다. => 트럼프가 이렇게 말 했다고 함.

        2. 문장 끝에 'ㅋㅋ' 또는 'ㄷㄷ' 을 가끔씩 넣어야 한다.
        ex) 북한이 갑자기 항복을 했다. => 북한이 갑자기 항복을 했다는 거임 ㅋㅋ (재밌거나 어이없는 소식)
        ex) 범인은 사실 A씨가 아닌 B씨 였다. => A가 아니라 B가 범인이였음 ㄷㄷ (놀라울만한 소식)

        3. 뉴스본문을 4 - 5 문장 이내로 간결하게 1, 2의 방법으로 요약한다. 각각의 문장은 매우 짧아야 한다. 다시, 각각의 문장은 매우 짧아야 한다. 뉴스 본문임을 표시하기 위해 '본문:'을 먼저 출력하고 요약문을 출력한다.

        4. 바로 다음줄 부터는 뉴스 내용에 대해 일반적인 {politics} 정치 성향을 가진 {age[0]}0대 {gender}성이 달만한 댓글을 출력한다. 간결하고 짧은 한문장으로 구성되며, 댓글의 수는 4개로 고정한다. 아래 예시 형식을 참고한다.
        
        댓글은 되도록 경박한, 비꼬는 말투를 사용한다. 또한 비판적으로 사고해야 한다. 그러나 거짓된 사실이 들어가서는 안된다. 간결하고 짧은 말투를 사용한다. 댓글 앞에는 항상 '댓글:'을 먼저 출력하고 댓글을 출력한다.

        ex1) 감정표현) 재미있을 때 : ㅋㅋㅋㅋㅋㅋ, 놀라울 때 : ㄷㄷㄷ 이거 진짜임?, 화나는 내용일 때 : 아 개빡치네...
        ex2) 뉴스 내용 되묻기(상세 설명 요청하기)) : ex) 왜 트럼프는 저렇게 말한거임?, ex) 그래서 이제 김모씨는 어떻게 되는거냐?
        (ex2)의 댓글의 바로 다음 댓글은 그에 대한 대답으로 고정한다.두 문장 까지 사용 가능하다) ex) 징역 15년 형 받고 감옥 체험중
        ex3) 뉴스에 공감 요청하기 : 형식 :  아 ㅋㅋ (공감을 유도하고자 하는 내용) + 일 것같으면 개추 ㅋㅋ 의 형식으로 사용. : ex) 아 ㅋㅋ 언젠간 이렇게 될 줄 알았으면 개추 ㅋㅋ, 아 ㅋㅋ 우리나라 경제 좆된거 같으면 개추 ㅋㅋ, 아 ㅋㅋ 이새끼 너무 추한거같으면 개추 ㅋㅋ
        (ex3)의 댓글의 바로 다음 댓글은 개추 ㅋㅋ 으로 고정한다.)
        ex4) 핵심 찌르기 : 뉴스의 핵심을 간파하고 내용을 설명한다 : 형식 : 팩트) ~~~이다. ex) 팩트) 이러다가 한국 좆되는거 순식간이다

        5. 뉴스 마다 구분을 위해 하나의 뉴스를 정리한 이후에는 -----을 출력

        6. 여기서 언급한 내용 이외의 쓸데없는 코멘트, 주석, 제목 등등 다양한 부가적인 것들은 달지마

        <예시 (요약문 5개 중 하나)>

        본문: 우리나라 이번에 미국한테 사기당한 듯. 북한이 미사일 쏘는데 미국이 자기만 알고 우리한테 안알려줌. 이거 완전 큰일 났다는 신호임 ㅋㅋ.

        댓글:아 ㅋㅋㅋㅋ 이제 우리나라 떠나야 할 것 같으면 개추 ㅋㅋ
        댓글:개추 ㅋㅋㅋㅋ
        댓글:이건 왜 이렇게 된거냐?
        댓글:트럼프가 공식 발표해서 이렇게 됨

        -----


        \n\n{all_contents}"""

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", 
                    "content": prompt}
                ],
                
            )
            if response.choices and response.choices[0].message:
                return response.choices[0].message.content.strip() 
            else:
                return "No completion found."
            
        # API 키 설정 및 요약문과 댓글 생성
        selected_summaries = summarize_and_generate_comments(all_articles)
        print(selected_summaries)


        import openai
        from gtts import gTTS
        from moviepy.editor import concatenate_audioclips, concatenate_videoclips, CompositeVideoClip, TextClip, ImageClip, AudioFileClip
        import os
        from pydub import AudioSegment


        # GPT로 생성한 요약 및 댓글 분리
        def extract_texts_and_comments(selected_summaries):
            lines = selected_summaries.split('\n')
            
            texts = []
            comments = []
            current_text = []
            current_comment = []
            reading_text = True

            for line in lines:
                if line.startswith("-----"):  # 뉴스 항목 구분
                    if current_text:
                        texts.append("\n".join(current_text)) #texts list : [i - 1] : i번째 뉴스 텍스트
                        current_text = []
                    if current_comment:
                        comments.append("\n".join(current_comment)) #comments list : [i - 1] : i번째 뉴스 댓글
                        current_comment = []
                    reading_text = True  # 새로운 뉴스 항목 시작
                elif line.startswith("본문:"):
                    reading_text = True
                    current_text.append(line[len("본문:"):].strip())
                elif line.startswith("댓글:"):
                    reading_text = False
                    current_comment.append(line[len("댓글:"):].strip())
                elif reading_text:
                    current_text.append(line.strip())
                else:
                    current_comment.append(line.strip())

            if current_text:
                texts.append("\n".join(current_text))
            if current_comment:
                comments.append("\n".join(current_comment))

            return texts, comments

        # DALL-E를 사용하여 이미지 생성
        def generate_images_for_news(texts, api_key):
            openai.api_key = api_key
            image_urls = []
            
            for text in texts:
                strT = f"{text}\n 이 텍스트와 어울리는 이미지를 DALL-E의 보안 규정에 맞게 잘 생성할 수 있도록 텍스트를 변환해서 그 텍스트만 출력해줘. 다시한번 말하지만 DALL-E가 거부하지 않고 생성할만한 텍스트야."
                response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", 
                    "content": strT}
                ],
                )
                res = response.choices[0].message.content.strip()
                response = client.images.generate(
                    model = "dall-e-3",
                    prompt=res,
                    n=1,
                    size="1024x1024",
                    quality="standard",
                )
                image_urls.append(response.data[0].url)
            return image_urls


        import requests
        from time import sleep

        def typecast_tts(text, actor_id, API_TOKEN):
            HEADERS = {'Authorization': f'Bearer {API_TOKEN}'}
            # 음성 합성 요청
            response = requests.post('https://typecast.ai/api/speak', headers=HEADERS, json={
                'text': text,
                'lang': 'auto',  # 언어 설정, 'ko'로 설정 가능
                'actor_id': actor_id,
                "tempo": 1.3,
                'xapi_hd': True,
                'model_version': 'latest'
            })
            speak_url = response.json()['result']['speak_v2_url']

            # 음성 합성 결과 폴링
            for _ in range(120):  # 최대 2분 대기
                response = requests.get(speak_url, headers=HEADERS)
                ret = response.json()['result']
                if ret['status'] == 'done':
                    # 음성 파일 다운로드
                    audio_response = requests.get(ret['audio_download_url'])
                    filename = f"tts_{hash(text)}.mp3"
                    with open(filename, 'wb') as f:
                        f.write(audio_response.content)
                    return filename
                sleep(1)
            return None

        import openai
        from gtts import gTTS
        from moviepy.editor import concatenate_audioclips, concatenate_videoclips, CompositeVideoClip,CompositeAudioClip, TextClip, ImageClip, AudioFileClip, VideoFileClip
        import os
        from pydub import AudioSegment
        from datetime import date

        def tts_and_duration_typecast(text, actor_id, API_TOKEN, lang='ko'):
            if not text.strip():
                return None, 0
            filename = typecast_tts(text, actor_id, API_TOKEN)
            audio_clip = AudioFileClip(filename)
            return audio_clip, audio_clip.duration



        def create_video_for_news(text, comment, image_url, template_image_path, output_filename):
            target_size = (1080, 1920)  # 세로 HD 포맷
            template_image = ImageClip(template_image_path).resize(newsize=target_size)
            
            desired_image_size = (600, 600)  # 원하는 이미지 크기 설정
            main_image = ImageClip(image_url).resize(newsize=desired_image_size).set_position((240, 400))

            sentences = text.split('. ')
            comments = comment.split('\n')
            audio_list = []
            duration_list = []

            actor_id = "6059dad0b83880769a50502f"

            # TTS 오디오 생성
            for content in sentences + comments:
                audio_clip, duration = tts_and_duration_typecast(content, actor_id, api)
                audio_list.append(audio_clip)
                duration_list.append(duration)

            total_duration = sum(duration_list)
            current_time = 0

            
            all_audios = []
            all_video_clips = [template_image.set_duration(total_duration), main_image.set_duration(total_duration)] 

            # 본문 자막 생성
            y_position = 1020  # 본문 자막의 시작 위치
            for idx, sentence in enumerate(sentences):
                if audio_list[idx]:
                    all_audios.append(audio_list[idx])
                    text_clip = TextClip(sentence, fontsize=35, color='black', font='나눔고딕-Bold')
                    text_clip = text_clip.set_position(('center', y_position)).set_start(current_time).set_duration(total_duration - current_time)
                    all_video_clips.append(text_clip)
                    y_position += 80  # 다음 문장의 위치 조정
                current_time += duration_list[idx]

            # 댓글 자막 생성
            y_position = 1550  # 댓글 자막의 시작 위치
            for comment_idx, comment in enumerate(comments, start=len(sentences)):
                if audio_list[comment_idx]:
                    all_audios.append(audio_list[comment_idx])
                    comment_clip = TextClip('└  '+comment, fontsize=33, color='black', font='나눔고딕-Bold')
                    comment_clip = comment_clip.set_position((170, y_position)).set_start(current_time).set_duration(total_duration - current_time)
                    all_video_clips.append(comment_clip)
                    y_position += 70  # 다음 댓글의 위치 조정
                current_time += duration_list[comment_idx]


            today = str(date.today())
            Title = '실시간 ' + today[5:7] + '월' + today[8:10] + '일' + '자 뉴스 근황 ㅋㅋㅋㅋ'

            date_clip = TextClip(Title, fontsize=55, color='black', font='나눔고딕-Bold')
            date_clip = date_clip.set_position((0, 180)).set_duration(total_duration)

            all_video_clips.append(date_clip)

            # 비디오 및 오디오 결합
            final_video = CompositeVideoClip(all_video_clips).set_duration(total_duration)
            final_audio = concatenate_audioclips(all_audios)

            # 최종 비디오 파일 생성
            #final_clip = final_video.set_audio(final_audio)

            return total_duration, final_video, final_audio

            #final_clip.write_videofile(output_filename, codec='mpeg4', fps=24)


        # API 키 설정 및 이미지 생성
        api_key = 'sk-proj-xw4GZLg51wMd6OiFs3IYT3BlbkFJ9HJApcN7LbYS3HjvDTme'
        texts, comments = extract_texts_and_comments(selected_summaries)
        image_urls = generate_images_for_news(texts, api_key)




        # 템플릿 이미지 경로

        Audio = []
        Video = []
        totaltime = 0

        # 각각의 뉴스를 위한 비디오 생성 및 저장
        for i, (text, comment, image_url) in enumerate(zip(texts, comments, image_urls)):
            print(text + '\n' +  comment)
            output_filename = f"news_video_{i+1}.avi"
            D, Vid, Aud = create_video_for_news(text, comment, image_url, template_image_path, output_filename)
            totaltime += D
            Video.append(Vid), Audio.append(Aud)


        Video_output = concatenate_videoclips(Video)
        bgm = AudioFileClip(bgm_link).set_duration(totaltime).volumex(0.5)
        Audio_output = CompositeAudioClip([concatenate_audioclips(Audio), bgm]).set_duration(totaltime)

        update_status('v1', "뉴스 크롤링 완료, 비디오 생성 중")
        
        final_clip = Video_output.set_audio(Audio_output)
        final_clip.write_videofile(f'newsGenerator_v1.avi', codec='mpeg4', fps=24) 
        update_status('v1', "비디오 생성 완료")
    
    elif (script_path == "nate"):
        import os
        from openai import OpenAI
        from openai import Image
        import requests
        from bs4 import BeautifulSoup
        
        template_image_path = os.path.join(static_folder, 'data', 'AIproject', 'AIproject', 'template_image_2.png')
        bgm_link = os.path.join(static_folder, 'data', 'AIproject', 'AIproject', 'If I Had a Chicken.mp3')

        client = OpenAI(
            # This is the default and can be omitted
            api_key="sk-proj-xw4GZLg51wMd6OiFs3IYT3BlbkFJ9HJApcN7LbYS3HjvDTme",
        )

        category_urls = {
            'economy': 'https://news.naver.com/main/list.naver?mode=LSD&mid=shm&sid1=101',  # 경제
            'politics': 'https://news.naver.com/main/list.naver?mode=LSD&mid=shm&sid1=100',  # 정치
            'society': 'https://news.naver.com/main/list.naver?mode=LSD&mid=shm&sid1=102'   # 사회
        }

        def get_article_content(article_url):
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(article_url, headers=headers)
            
            if response.status_code == 200:
                html = response.text
                soup = BeautifulSoup(html, 'html.parser')
                
                # 기사 제목
                title_tag = soup.find('h2', class_='media_end_head_headline')
                title = title_tag.text.strip() if title_tag else '제목 없음'
                
                # 기사 본문
                content_tag = soup.find('div', id='newsct_article', class_='newsct_article _article_body')
                content = content_tag.text.strip() if content_tag else '본문 없음'
                
                return title, content
            else:
                return None, None

        def get_news_from_category(category, url):
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                html = response.text
                soup = BeautifulSoup(html, 'html.parser')
                
                news_list = soup.find_all('ul', class_='type06_headline')
                articles = news_list[0].find_all('li') if news_list else []
                
                data = []
                
                for article in articles:
                    try:
                        link_tag = article.find('a')
                        link = link_tag['href']
                        title, content = get_article_content(link)
                        if title and content:
                            data.append({'Category': category, 'Title': title, 'Content': content})
                            print(f"제목: {title}\n본문: {content}\n링크: {link}\n")
                    except Exception as e:
                        print("Error parsing article:", e)
                        
                return data
            else:
                print("Failed to retrieve the web page. Status code:", response.status_code)
                return []

        # 카테고리별 기사 크롤링
        all_articles = []
        for category, url in category_urls.items():
            articles = get_news_from_category(category, url)
            all_articles.extend(articles)

        # 크롤링한 데이터 확인
        for article in all_articles:
            print(f"Category: {article['Category']}\nTitle: {article['Title']}\nContent: {article['Content']}\n")

        # OpenAI GPT-4 API를 사용하여 뉴스 요약 및 댓글 생성
        def summarize_and_generate_comments(articles, top_n=5):
            all_contents = "\n\n".join([article['Content'] for article in articles])
            
            prompt = f"""다음 뉴스 기사들을 읽은 후 가장 흥미롭고, 자극적이며, 사회비판적인 중요한 5개의 기사를 선별하여 아래 과정을 수행해.

        다음 뉴스를 핵심 내용으로 요약해줘. 요약문은 아래 내용을 바탕으로 경박한 말투로 작성해.

        1. ~~하다 => 라고함. ~~이다 => 임. ~~했다 => ~~했다고 함. ~~였다 => ~~였던거임. 으로 바꿔서 작성해야 한다. 
        즉, 누군가에게 소식을 듣고 전하듯 말하면서, 말 끝은 ~~함,임으로 끝낸다.
        ex) 트럼프 대통령은 다음 말을 전했다. => 트럼프가 이렇게 말 했음.

        2. 문장 끝에 'ㅠㅠ' 또는 'ㄷㄷ' 을 가끔씩 넣어야 한다.
        ex) 남주가 갑자기 항복을 했다. => 남주가 갑자기 항복을 했다는 거임 ㅠㅠ (슬프거나 안타까운 소식)
        ex) 범인은 사실 A씨가 아닌 B씨 였다. => A가 아니라 B가 범인이였음 ㄷㄷ (놀라울만한 소식)

        3. 뉴스본문을 4 - 5 문장 이내로 간결하게 1, 2의 방법으로 요약한다. 각각의 문장은 짧아야 한다. 뉴스 본문임을 표시하기 위해 '본문:'을 먼저 출력하고 요약문을 출력한다.

        4. 바로 다음줄 부터는 뉴스 내용에 대해 일반적인 {politics} 정치 성향을 가진 {age[0]}0대 {gender}성이 달만한 댓글을 출력한다. 간결하고 짧은 한문장으로 구성되며, 댓글의 수는 4개로 고정한다. 아래 예시 형식을 참고한다.

        댓글은 되도록 어딘가 마음에 안들어하는 듯한 말투를 사용한다. 또한 비판적으로 사고해야 한다. 그러나 거짓된 사실이 들어가서는 안된다. 간결하고 짧은 말투를 사용한다. 댓글 앞에는 항상 '댓글:'을 먼저 출력하고 댓글을 출력한다.

        ex1) 감정표현) 재미있을 때 : ㅋㅋㅋㅋㅋㅋ, 놀라울 때 : ㄷㄷㄷ 이거 진짜야?, 화나는 내용일 때 : 아 개빡치네...
        ex2) 뉴스 내용 되묻기(상세 설명 요청하기)) : ex) 왜 트럼프는 저렇게 말한거야?, ex) 쓰니야 그래서 이제 김모씨는 어떻게 되는거야?
        (ex2)의 댓글의 바로 다음 댓글은 그에 대한 대답으로 고정한다.두 문장 까지 사용 가능하다) ex) 징역 15년 형 받고 감옥 체험중이야 ㅠㅠ
        ex3) 뉴스에 공감 요청하기 : 형식 : 공감하는  : ex) 우리나라 이제 어떡해?? ex) 쓰니야 우리나라 이제 망한거 아니야? ㅠㅠ
        (ex3)의 댓글의 바로 다음 댓글은 그니까 퓨ㅠㅠ 으로 고정한다.)
        ex4) 핵심 찌르기 : 뉴스의 핵심을 간파하고 내용을 설명한다 : 형식 : 솔직히 ~~~이라고 생각해. ex) 팩트) 솔직히 이러다가 한국 끝나는거 순식간이라고 생각해.

        5. 뉴스 마다 구분을 위해 하나의 뉴스를 정리한 이후에는 -----을 출력

        6. 여기서 언급한 내용 이외의 쓸데없는 코멘트, 주석, 제목 등등 다양한 부가적인 것들은 달지마

        <예시 (요약문 5개 중 하나)>

        본문: 우리나라 이번에 미국한테 사기당한 듯. 북한이 미사일 쏘는데 미국이 자기만 알고 우리한테 안알려준대 ㅠㅠ. 이거 완전 큰일 났다는 신호야...

        댓글: 어떡해? 우리나라 이제 완전 망한거 아니야?
        댓글: 그니까 퓨ㅠㅠ
        댓글: 이건 왜 이렇게 된거야?
        댓글: 트럼프가 공식 발표해서 이렇게 됐음...

        -----


        \n\n{all_contents}"""

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", 
                    "content": prompt}
                ],
                
            )
            if response.choices and response.choices[0].message:
                return response.choices[0].message.content.strip() 
            else:
                return "No completion found."
            
        # API 키 설정 및 요약문과 댓글 생성
        selected_summaries = summarize_and_generate_comments(all_articles)
        print(selected_summaries)


        import openai
        from gtts import gTTS
        from moviepy.editor import concatenate_audioclips, concatenate_videoclips, CompositeVideoClip, TextClip, ImageClip, AudioFileClip
        import os
        from pydub import AudioSegment


        # GPT로 생성한 요약 및 댓글 분리
        def extract_texts_and_comments(selected_summaries):
            lines = selected_summaries.split('\n')
            
            texts = []
            comments = []
            current_text = []
            current_comment = []
            reading_text = True

            for line in lines:
                if line.startswith("-----"):  # 뉴스 항목 구분
                    if current_text:
                        texts.append("\n".join(current_text)) #texts list : [i - 1] : i번째 뉴스 텍스트
                        current_text = []
                    if current_comment:
                        comments.append("\n".join(current_comment)) #comments list : [i - 1] : i번째 뉴스 댓글
                        current_comment = []
                    reading_text = True  # 새로운 뉴스 항목 시작
                elif line.startswith("본문:"):
                    reading_text = True
                    current_text.append(line[len("본문:"):].strip())
                elif line.startswith("댓글:"):
                    reading_text = False
                    current_comment.append(line[len("댓글:"):].strip())
                elif reading_text:
                    current_text.append(line.strip())
                else:
                    current_comment.append(line.strip())

            if current_text:
                texts.append("\n".join(current_text))
            if current_comment:
                comments.append("\n".join(current_comment))

            return texts, comments

        # DALL-E를 사용하여 이미지 생성
        def generate_images_for_news(texts, api_key):
            openai.api_key = api_key
            image_urls = []
            
            for text in texts:
                strT = f"{text}\n 이 텍스트와 어울리는 이미지를 DALL-E의 보안 규정에 맞게 잘 생성할 수 있도록 텍스트를 변환해서 그 텍스트만 출력해줘. 다시한번 말하지만 DALL-E가 거부하지 않고 생성할만한 텍스트야."
                response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", 
                    "content": strT}
                ],
                )
                res = response.choices[0].message.content.strip()
                response = client.images.generate(
                    model = "dall-e-3",
                    prompt=res,
                    n=1,
                    size="1024x1024",
                    quality="standard",
                )
                image_urls.append(response.data[0].url)
            return image_urls


        import requests
        from time import sleep

        def typecast_tts(text, actor_id, API_TOKEN):
            HEADERS = {'Authorization': f'Bearer {API_TOKEN}'}
            # 음성 합성 요청
            response = requests.post('https://typecast.ai/api/speak', headers=HEADERS, json={
                'text': text,
                'lang': 'auto',  # 언어 설정, 'ko'로 설정 가능
                'actor_id': actor_id,
                "tempo": 1.3,
                'xapi_hd': True,
                'model_version': 'latest'
            })
            speak_url = response.json()['result']['speak_v2_url']

            # 음성 합성 결과 폴링
            for _ in range(120):  # 최대 2분 대기
                response = requests.get(speak_url, headers=HEADERS)
                ret = response.json()['result']
                if ret['status'] == 'done':
                    # 음성 파일 다운로드
                    audio_response = requests.get(ret['audio_download_url'])
                    filename = f"tts_{hash(text)}.mp3"
                    with open(filename, 'wb') as f:
                        f.write(audio_response.content)
                    return filename
                sleep(1)
            return None

        import openai
        from gtts import gTTS
        from moviepy.editor import concatenate_audioclips, concatenate_videoclips, CompositeVideoClip,CompositeAudioClip, TextClip, ImageClip, AudioFileClip, VideoFileClip
        import os
        from pydub import AudioSegment
        from datetime import date

        def tts_and_duration_typecast(text, actor_id, API_TOKEN, lang='ko'):
            if not text.strip():
                return None, 0
            filename = typecast_tts(text, actor_id, API_TOKEN)
            audio_clip = AudioFileClip(filename)
            return audio_clip, audio_clip.duration



        def create_video_for_news(text, comment, image_url, template_image_path, output_filename):
            target_size = (1080, 1920)  # 세로 HD 포맷
            template_image = ImageClip(template_image_path).resize(newsize=target_size)
            
            desired_image_size = (600, 600)  # 원하는 이미지 크기 설정
            main_image = ImageClip(image_url).resize(newsize=desired_image_size).set_position((240, 400))

            sentences = text.split('. ')
            comments = comment.split('\n')
            audio_list = []
            duration_list = []

            actor_id = "611c3f692fac944dff493a04"

            # TTS 오디오 생성
            for content in sentences + comments:
                audio_clip, duration = tts_and_duration_typecast(content, actor_id, api)
                audio_list.append(audio_clip)
                duration_list.append(duration)

            total_duration = sum(duration_list)
            current_time = 0

            
            all_audios = []
            all_video_clips = [template_image.set_duration(total_duration), main_image.set_duration(total_duration)] 

            # 본문 자막 생성
            y_position = 1020  # 본문 자막의 시작 위치
            for idx, sentence in enumerate(sentences):
                if audio_list[idx]:
                    all_audios.append(audio_list[idx])
                    text_clip = TextClip(sentence, fontsize=35, color='black', font='나눔고딕-Bold')
                    text_clip = text_clip.set_position(('center', y_position)).set_start(current_time).set_duration(total_duration - current_time)
                    all_video_clips.append(text_clip)
                    y_position += 80  # 다음 문장의 위치 조정
                current_time += duration_list[idx]

            # 댓글 자막 생성
            y_position = 1503  # 댓글 자막의 시작 위치
            for comment_idx, comment in enumerate(comments, start=len(sentences)):
                if audio_list[comment_idx]:
                    all_audios.append(audio_list[comment_idx])
                    comment_clip = TextClip('└  '+comment, fontsize=33, color='black', font='나눔고딕-Bold')
                    comment_clip = comment_clip.set_position((170, y_position)).set_start(current_time).set_duration(total_duration - current_time)
                    all_video_clips.append(comment_clip)
                    y_position += 109  # 다음 댓글의 위치 조정
                current_time += duration_list[comment_idx]


            today = str(date.today())
            Title = today[5:7] + '월' + today[8:10] + '일' + ' 뉴스 ㄹㅇ 소름인 점'

            date_clip = TextClip(Title, fontsize=55, color='black', font='나눔고딕-Bold')
            date_clip = date_clip.set_position((200, 85)).set_duration(total_duration)

            all_video_clips.append(date_clip)

            # 비디오 및 오디오 결합
            final_video = CompositeVideoClip(all_video_clips).set_duration(total_duration)
            final_audio = concatenate_audioclips(all_audios)

            # 최종 비디오 파일 생성
            #final_clip = final_video.set_audio(final_audio)

            return total_duration, final_video, final_audio

            #final_clip.write_videofile(output_filename, codec='mpeg4', fps=24)


        # API 키 설정 및 이미지 생성
        api_key = 'sk-proj-xw4GZLg51wMd6OiFs3IYT3BlbkFJ9HJApcN7LbYS3HjvDTme'
        texts, comments = extract_texts_and_comments(selected_summaries)
        image_urls = generate_images_for_news(texts, api_key)
        
        Audio = []
        Video = []
        totaltime = 0

        # 각각의 뉴스를 위한 비디오 생성 및 저장
        for i, (text, comment, image_url) in enumerate(zip(texts, comments, image_urls)):
            print(text + '\n' +  comment)
            output_filename = f"news_video_{i+1}.avi"
            D, Vid, Aud = create_video_for_news(text, comment, image_url, template_image_path, output_filename)
            totaltime += D
            Video.append(Vid), Audio.append(Aud)


        Video_output = concatenate_videoclips(Video)
        bgm = AudioFileClip(bgm_link).set_duration(totaltime).volumex(0.5)
        Audio_output = CompositeAudioClip([concatenate_audioclips(Audio), bgm]).set_duration(totaltime)

        final_clip = Video_output.set_audio(Audio_output)
        final_clip.write_videofile(f'newsGenerator_v1.avi', codec='mpeg4', fps=24) 

@app.route('/crawl_news', methods=['POST'])
def handle_crawl_news():
    script_path = request.form.get('script_path')
    gender = request.form.get('gender')
    politics = request.form.get('politics')
    age = request.form.get('age')
    video_filename = f'newsGenerator_v1.avi'
    output_filename = crawl_news(script_path, gender, politics, age, video_filename)
    download_link = f"/download/v1"
    return f'<a href="{download_link}">Download your video</a>'

import sys
if __name__ == '__main__':
    script_path = sys.argv[1]
    gender = sys.argv[2]
    politics = sys.argv[3]
    age = sys.argv[4]
    crawl_news(script_path, gender, politics, age)
