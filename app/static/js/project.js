// 이메일 발송 함수
function sendEmail(emailType) {
    const projectId = document.querySelector('[data-project-id]').dataset.projectId;
    
    fetch(`/project/${projectId}/mail/${emailType}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('이메일이 성공적으로 발송되었습니다.');
            location.reload();
        } else {
            alert('이메일 발송에 실패했습니다: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('이메일 발송 중 오류가 발생했습니다.');
    });
}

// 상태 업데이트 함수
function updateStatus(newStatus) {
    const projectId = document.querySelector('[data-project-id]').dataset.projectId;
    
    fetch(`/project/${projectId}/status`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            status: newStatus
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert('상태 변경에 실패했습니다: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('상태 변경 중 오류가 발생했습니다.');
    });
}

// 취소 모달 관련 함수들
function showCancelModal() {
    const modal = new bootstrap.Modal(document.getElementById('cancelModal'));
    modal.show();
}

function cancelProject() {
    const projectId = document.querySelector('[data-project-id]').dataset.projectId;
    const cancelReason = document.getElementById('cancelReason').value.trim();
    
    if (!cancelReason) {
        alert('취소 사유를 입력해주세요.');
        return;
    }
    
    fetch(`/project/${projectId}/cancel`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            cancel_reason: cancelReason
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert('프로젝트 취소에 실패했습니다: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('프로젝트 취소 중 오류가 발생했습니다.');
    });
}

// 기간 연장 모달 관련 함수들
function showExtendModal() {
    const modal = new bootstrap.Modal(document.getElementById('extendModal'));
    modal.show();
}

function extendProject() {
    const projectId = document.querySelector('[data-project-id]').dataset.projectId;
    const newDate = document.getElementById('newDate').value;
    
    if (!newDate) {
        alert('새로운 완료 예정일을 선택해주세요.');
        return;
    }
    
    fetch(`/project/${projectId}/extend`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            new_date: newDate
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert('기간 연장에 실패했습니다: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('기간 연장 중 오류가 발생했습니다.');
    });
}

// 리포트 업로드 모달 관련 함수들
function showReportModal() {
    const modal = new bootstrap.Modal(document.getElementById('reportModal'));
    modal.show();
}

function uploadReport() {
    const projectId = document.querySelector('[data-project-id]').dataset.projectId;
    const reportFile = document.getElementById('reportFile').files[0];
    
    if (!reportFile) {
        alert('리포트 파일을 선택해주세요.');
        return;
    }
    
    const formData = new FormData();
    formData.append('report', reportFile);
    
    fetch(`/project/${projectId}/report`, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert('리포트 업로드에 실패했습니다: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('리포트 업로드 중 오류가 발생했습니다.');
    });
} 