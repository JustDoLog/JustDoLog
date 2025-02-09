// 좋아요 버튼 클릭 이벤트 핸들러
document.body.addEventListener('htmx:afterRequest', function(evt) {
    if (evt.detail.target && evt.detail.target.classList.contains('like-button')) {
        try {
            if (evt.detail.xhr.status === 400) {
                // 에러 응답(자신의 글 좋아요 등)의 경우 UI 업데이트하지 않음
                console.error('Error:', JSON.parse(evt.detail.xhr.response).error);
                return;
            }
            
            const data = JSON.parse(evt.detail.xhr.response);
            const button = evt.detail.target;
            const article = button.closest('article');
            
            // 좋아요 상태에 따라 버튼 스타일 변경
            if (data.liked) {
                button.classList.add('text-gray-900');
                button.classList.remove('text-gray-500');
                button.querySelector('svg').setAttribute('fill', 'currentColor');
            } else {
                button.classList.remove('text-gray-900');
                button.classList.add('text-gray-500');
                button.querySelector('svg').setAttribute('fill', 'none');
            }
            
            // 좋아요 수 업데이트
            button.querySelector('.likes-count').textContent = data.likes_count;
            
            // 메타 정보의 좋아요 수 업데이트
            // 게시글 목록 페이지의 경우
            if (article) {
                article.querySelector('.post-likes-count').textContent = '좋아요 ' + data.likes_count;
            }
            // 상세 페이지의 경우
            else {
                document.querySelector('.post-likes-count').textContent = data.likes_count;
            }
        } catch (error) {
            console.error('Error processing response:', error);
        }
    }
}); 