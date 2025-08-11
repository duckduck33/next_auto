'use client';

import React, { useState, useEffect } from 'react';
import Card from '../common/Card';
import Button from '../common/Button';

const BACKEND_URL = 'https://146.56.98.210:443';

export default function SessionManager({ onSessionChange }) {
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // 로컬 스토리지에서 현재 세션 ID 불러오기
    const savedSessionId = localStorage.getItem('currentSessionId');
    if (savedSessionId) {
      setCurrentSessionId(savedSessionId);
    }
    
    // 세션 목록 불러오기
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/sessions`);
      if (response.ok) {
        const data = await response.json();
        setSessions(data.sessions || []);
      }
    } catch (error) {
      console.error('세션 목록 로드 실패:', error);
    }
  };

  const createNewSession = async () => {
    setIsLoading(true);
    try {
      // 로컬 스토리지에서 설정 불러오기
      const savedSettings = localStorage.getItem('tvAutoSettings');
      if (!savedSettings) {
        alert('먼저 설정을 저장해주세요.');
        return;
      }

      const settings = JSON.parse(savedSettings);
      
      const response = await fetch(`${BACKEND_URL}/api/create-session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          apiKey: settings.apiKey,
          secretKey: settings.secretKey,
          exchangeType: settings.exchangeType,
          investment: settings.investment,
          leverage: settings.leverage,
          takeProfit: settings.takeProfit,
          stopLoss: settings.stopLoss,
          indicator: settings.indicator
        })
      });

      if (response.ok) {
        const data = await response.json();
        const newSessionId = data.session_id;
        
        // 새 세션을 현재 세션으로 설정
        setCurrentSessionId(newSessionId);
        localStorage.setItem('currentSessionId', newSessionId);
        
        // 세션 목록 새로고침
        await loadSessions();
        
        // 부모 컴포넌트에 세션 변경 알림
        if (onSessionChange) {
          onSessionChange(newSessionId);
        }
        
        alert('새 세션이 생성되었습니다.');
      } else {
        alert('세션 생성에 실패했습니다.');
      }
    } catch (error) {
      console.error('세션 생성 오류:', error);
      alert('세션 생성 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  const switchSession = async (sessionId) => {
    setCurrentSessionId(sessionId);
    localStorage.setItem('currentSessionId', sessionId);
    
    // 부모 컴포넌트에 세션 변경 알림
    if (onSessionChange) {
      onSessionChange(sessionId);
    }
    
    alert('세션이 변경되었습니다.');
  };

  const deleteSession = async (sessionId) => {
    if (!confirm('정말로 이 세션을 삭제하시겠습니까?')) {
      return;
    }

    try {
      const response = await fetch(`${BACKEND_URL}/api/session/${sessionId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        // 현재 세션이 삭제된 경우 세션 ID 초기화
        if (sessionId === currentSessionId) {
          setCurrentSessionId(null);
          localStorage.removeItem('currentSessionId');
          
          if (onSessionChange) {
            onSessionChange(null);
          }
        }
        
        // 세션 목록 새로고침
        await loadSessions();
        
        alert('세션이 삭제되었습니다.');
      } else {
        alert('세션 삭제에 실패했습니다.');
      }
    } catch (error) {
      console.error('세션 삭제 오류:', error);
      alert('세션 삭제 중 오류가 발생했습니다.');
    }
  };

  const getExchangeTypeLabel = (exchangeType) => {
    return exchangeType === 'demo' ? '데모 (VST)' : '실제 (USDT)';
  };

  const getIndicatorLabel = (indicator) => {
    return indicator === 'PREMIUM' ? '프리미엄지표' : '콘볼지표';
  };

  return (
    <Card title="세션 관리">
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h3 className="text-lg font-semibold text-white">활성 세션</h3>
          <Button 
            onClick={createNewSession} 
            disabled={isLoading}
            className="bg-green-600 hover:bg-green-700"
          >
            {isLoading ? '생성 중...' : '새 세션 생성'}
          </Button>
        </div>

        {sessions.length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            <p>활성 세션이 없습니다.</p>
            <p className="text-sm mt-2">새 세션을 생성하여 자동매매를 시작하세요.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {sessions.map((session) => (
              <div 
                key={session.session_id} 
                className={`p-4 rounded-lg border ${
                  session.session_id === currentSessionId 
                    ? 'border-blue-500 bg-blue-500/10' 
                    : 'border-gray-600 bg-gray-800'
                }`}
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="text-sm font-medium text-gray-300">
                        세션 ID: {session.session_id.slice(0, 8)}...
                      </span>
                      {session.session_id === currentSessionId && (
                        <span className="px-2 py-1 bg-blue-600 text-white text-xs rounded">
                          현재 세션
                        </span>
                      )}
                    </div>
                    
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span className="text-gray-400">거래소:</span>
                        <span className="ml-2 text-white">
                          {getExchangeTypeLabel(session.exchange_type)}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-400">지표:</span>
                        <span className="ml-2 text-white">
                          {getIndicatorLabel(session.indicator)}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-400">자동매매:</span>
                        <span className={`ml-2 ${session.is_auto_trading_enabled ? 'text-green-500' : 'text-red-500'}`}>
                          {session.is_auto_trading_enabled ? '활성화' : '비활성화'}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-400">현재 심볼:</span>
                        <span className="ml-2 text-white">
                          {session.current_symbol || '없음'}
                        </span>
                      </div>
                    </div>
                    
                    <div className="mt-2 text-xs text-gray-500">
                      마지막 활동: {new Date(session.last_activity).toLocaleString()}
                    </div>
                  </div>
                  
                  <div className="flex space-x-2 ml-4">
                    {session.session_id !== currentSessionId && (
                      <Button
                        onClick={() => switchSession(session.session_id)}
                        className="bg-blue-600 hover:bg-blue-700 text-xs px-3 py-1"
                      >
                        선택
                      </Button>
                    )}
                    <Button
                      onClick={() => deleteSession(session.session_id)}
                      variant="danger"
                      className="text-xs px-3 py-1"
                    >
                      삭제
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {currentSessionId && (
          <div className="mt-4 p-3 bg-gray-800 rounded-lg">
            <p className="text-sm text-gray-400">현재 세션</p>
            <p className="text-sm font-semibold text-white">
              {currentSessionId.slice(0, 8)}...
            </p>
            <p className="text-xs text-gray-500 mt-1">
              이 세션으로 자동매매가 실행됩니다.
            </p>
          </div>
        )}
      </div>
    </Card>
  );
}
