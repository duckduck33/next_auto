'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import SettingsForm from '../../components/SettingsForm';
import ProfitMonitor from '../../components/ProfitMonitor';

export default function Dashboard() {
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [isAutoTradingEnabled, setIsAutoTradingEnabled] = useState(false);
  const [userEmail, setUserEmail] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    // 로그인 상태 확인
    const isLoggedIn = localStorage.getItem('isLoggedIn');
    const savedUserEmail = localStorage.getItem('userEmail');
    
    if (isLoggedIn !== 'true') {
      router.push('/login');
      return;
    }
    
    setUserEmail(savedUserEmail || '사용자');
    setIsLoading(false);
  }, [router]);

  const handleLogout = () => {
    // 로그아웃 시 모든 로컬 스토리지 데이터 삭제
    localStorage.removeItem('isLoggedIn');
    localStorage.removeItem('userEmail');
    localStorage.removeItem('loginTime');
    localStorage.removeItem('tvAutoSettings');
    localStorage.removeItem('tvAutoStatus');
    
    router.push('/login');
  };

  const handleSessionChange = (sessionId) => {
    setCurrentSessionId(sessionId);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-white">로딩 중...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <div className="container mx-auto px-4 py-8">
        <header className="text-center mb-8">
          <div className="flex justify-between items-center mb-4">
            <div></div>
            <div className="flex items-center space-x-4">
              <span className="text-gray-400">안녕하세요, {userEmail}님</span>
              <button
                onClick={handleLogout}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm transition-colors"
              >
                로그아웃
              </button>
            </div>
          </div>
          
          <h1 className="text-4xl font-bold text-white mb-2">
            Next Auto Trading
          </h1>
          <p className="text-gray-400 mb-4">
            TradingView 자동매매 시스템
          </p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* 왼쪽 컬럼 */}
          <div className="space-y-6">
            <SettingsForm 
              onSettingsChange={handleSessionChange} 
              onAutoTradingChange={setIsAutoTradingEnabled}
            />
          </div>

          {/* 오른쪽 컬럼 */}
          <div className="space-y-6">
            <ProfitMonitor
              sessionId={currentSessionId}
              isAutoTradingEnabled={isAutoTradingEnabled}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
