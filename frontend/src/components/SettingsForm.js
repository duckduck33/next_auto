'use client';

import React, { useState, useEffect } from 'react';
import Card from './common/Card';
import Input from './common/Input';
import Button from './common/Button';
import Dropdown from './common/Dropdown';

const DEFAULT_SETTINGS = {
  apiKey: '',
  secretKey: '',
  exchangeType: 'demo', // 'demo' or 'live'
  investment: 1000,
  leverage: 10,
  takeProfit: 2,
  stopLoss: 2,
  indicator: 'PREMIUM',
  isAutoTradingEnabled: false
};

const INDICATOR_OPTIONS = [
  { value: 'PREMIUM', label: '프리미엄지표' },
  { value: 'CONBOL', label: '콘볼지표' }
];

const EXCHANGE_OPTIONS = [
  { value: 'demo', label: '데모 거래소 (VST)' },
  { value: 'live', label: '실제 거래소 (USDT)' }
];

export default function SettingsForm({ onSettingsChange, onAutoTradingChange }) {
  const [isRunning, setIsRunning] = useState(false);
  const [settings, setSettings] = useState(DEFAULT_SETTINGS);
  const [isLoading, setIsLoading] = useState(false);
  const [serverStatus, setServerStatus] = useState('checking');
  const [isSettingsSaved, setIsSettingsSaved] = useState(false);

  useEffect(() => {
    // 로컬 스토리지에서 설정 불러오기
    const savedSettings = localStorage.getItem('tvAutoSettings');
    const savedStatus = localStorage.getItem('tvAutoStatus');
    
    if (savedSettings) {
      const parsedSettings = JSON.parse(savedSettings);
      setSettings(parsedSettings);
      setIsSettingsSaved(true);
    }
    if (savedStatus) {
      setIsRunning(JSON.parse(savedStatus));
    }

    // 백엔드 서버 상태 확인
    checkServerStatus();
  }, []);

  const checkServerStatus = async () => {
    try {
      const response = await fetch('/api/settings');
      if (response.ok) {
        setServerStatus('connected');
      } else {
        setServerStatus('error');
      }
    } catch (error) {
      console.error('서버 연결 실패:', error);
      setServerStatus('error');
    }
  };

  const handleSave = async () => {
    setIsLoading(true);
    try {
      // 로컬 스토리지에 저장
      localStorage.setItem('tvAutoSettings', JSON.stringify(settings));
      
      // 안전한 숫자 변환 함수
      const safeParseFloat = (value, defaultValue = 0) => {
        const parsed = parseFloat(value);
        return isNaN(parsed) ? defaultValue : parsed;
      };
      
      const safeParseInt = (value, defaultValue = 0) => {
        const parsed = parseInt(value);
        return isNaN(parsed) ? defaultValue : parsed;
      };
      
      // 현재 로그인된 사용자 이메일 가져오기
      const userEmail = localStorage.getItem('userEmail');
      
      // 세션 생성/업데이트
      const requestBody = {
        userEmail: userEmail,
        apiKey: settings.apiKey,
        secretKey: settings.secretKey,
        exchangeType: settings.exchangeType,
        investment: safeParseFloat(settings.investment, 1000),
        leverage: safeParseInt(settings.leverage, 10),
        takeProfit: safeParseFloat(settings.takeProfit, 2),
        stopLoss: safeParseFloat(settings.stopLoss, 2),
        indicator: settings.indicator,
        isAutoTradingEnabled: isRunning
      };
      
      console.log('세션 생성 요청:', requestBody);
      
      const response = await fetch(`/api/create-or-update-session`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(requestBody)
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('세션 생성 성공:', data);
        
        // 거래소 타입을 로컬 스토리지에 저장
        localStorage.setItem('exchangeType', settings.exchangeType);
        
        if (onSettingsChange) {
          onSettingsChange(data.session_id);
        }
        
        setIsSettingsSaved(true);
      } else {
        const errorText = await response.text();
        console.error('세션 생성 실패:', errorText);
        alert(`세션 생성 중 오류가 발생했습니다: ${errorText}`);
      }
    } catch (error) {
      console.error('설정 저장 중 오류:', error);
      alert(`설정 저장 중 오류가 발생했습니다: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleAutoTrading = async () => {
    const newStatus = !isRunning;
    
    // 백엔드에 자동매매 상태 업데이트
    try {
      const response = await fetch(`/api/create-or-update-session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userEmail: localStorage.getItem('userEmail'),
          apiKey: settings.apiKey,
          secretKey: settings.secretKey,
          exchangeType: settings.exchangeType,
          investment: parseFloat(settings.investment),
          leverage: parseInt(settings.leverage),
          takeProfit: parseFloat(settings.takeProfit),
          stopLoss: parseFloat(settings.stopLoss),
          indicator: settings.indicator,
          isAutoTradingEnabled: newStatus
        })
      });
      
      if (!response.ok) {
        console.error('자동매매 상태 업데이트 실패:', response.status);
        alert('자동매매 상태 업데이트 중 오류가 발생했습니다.');
        return;
      } else {
        setIsRunning(newStatus);
        localStorage.setItem('tvAutoStatus', JSON.stringify(newStatus));
        
        if (onAutoTradingChange) {
          onAutoTradingChange(newStatus);
        }
        
        alert(newStatus ? '자동매매가 활성화되었습니다.' : '자동매매가 비활성화되었습니다.');
      }
    } catch (error) {
      console.error('자동매매 상태 업데이트 중 오류:', error);
      alert('자동매매 상태 업데이트 중 오류가 발생했습니다.');
    }
  };

  // 테스트용 리플 롱 포지션 진입
  const handleTestLongPosition = async () => {
    if (!isSettingsSaved) {
      alert('먼저 설정을 저장해주세요.');
      return;
    }

    if (!confirm('리플 롱 포지션을 진입하시겠습니까?')) {
      return;
    }

    try {
      const sessionId = `${localStorage.getItem('userEmail')}_${settings.exchangeType}`;
      
      const response = await fetch(`/api/test-long-position`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId })
      });

      const data = await response.json();
      
      if (response.ok && data.success) {
        alert('✅ 리플 롱 포지션 진입 완료!');
        console.log('테스트 거래 결과:', data);
      } else {
        alert(`❌ 포지션 진입 실패: ${data.detail || data.message}`);
      }
    } catch (error) {
      console.error('테스트 거래 오류:', error);
      alert('테스트 거래 중 오류가 발생했습니다.');
    }
  };

  // 긴급 청산
  const handleEmergencyClose = async () => {
    if (!isSettingsSaved) {
      alert('먼저 설정을 저장해주세요.');
      return;
    }

    if (!confirm('🚨 모든 포지션을 긴급 청산하시겠습니까?\n\n이 작업은 되돌릴 수 없습니다!')) {
      return;
    }

    try {
      const sessionId = `${localStorage.getItem('userEmail')}_${settings.exchangeType}`;
      
      const response = await fetch(`/api/emergency-close-all`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId })
      });

      const data = await response.json();
      
      if (response.ok && data.success) {
        alert(`✅ 긴급 청산 완료!\n\n${data.message}`);
        console.log('긴급 청산 결과:', data);
      } else {
        alert(`❌ 긴급 청산 실패: ${data.detail || data.message}`);
      }
    } catch (error) {
      console.error('긴급 청산 오류:', error);
      alert('긴급 청산 중 오류가 발생했습니다.');
    }
  };

  return (
    <Card title="빙엑스 트레이딩뷰 자동매매 설정">
      <div className="space-y-4">
        {/* 서버 상태 표시 */}
        <div className={`p-3 rounded-lg text-sm ${
          serverStatus === 'connected' ? 'bg-green-900 text-green-200' :
          serverStatus === 'error' ? 'bg-red-900 text-red-200' :
          'bg-yellow-900 text-yellow-200'
        }`}>
          {serverStatus === 'connected' && '✅ 백엔드 서버 연결됨'}
          {serverStatus === 'error' && '❌ 백엔드 서버 연결 실패'}
          {serverStatus === 'checking' && '⏳ 서버 상태 확인 중...'}
        </div>

        <Input
          type="text"
          label="API 키"
          value={settings.apiKey}
          onChange={(value) => setSettings({ ...settings, apiKey: value })}
        />
        <Input
          type="password"
          label="시크릿 키"
          value={settings.secretKey}
          onChange={(value) => setSettings({ ...settings, secretKey: value })}
        />
        <Dropdown
          label="거래소 선택"
          value={settings.exchangeType}
          onChange={(value) => setSettings({ ...settings, exchangeType: value })}
          options={EXCHANGE_OPTIONS}
        />
        
        {/* 거래 설정 */}
        <div className="border border-gray-600 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-white mb-4">
            {settings.exchangeType === 'demo' ? '📊 데모 거래소' : '💰 실제 거래소'} 거래 설정
          </h3>
          <div className="grid grid-cols-2 gap-4">
            <Input
              type="number"
              label={`투자금액 (${settings.exchangeType === 'demo' ? 'VST' : 'USDT'})`}
              value={settings.investment}
              onChange={(value) => setSettings({...settings, investment: Number(value)})}
              placeholder="1000"
            />
            <Input
              type="number"
              label="레버리지"
              value={settings.leverage}
              onChange={(value) => setSettings({...settings, leverage: Number(value)})}
              placeholder="10"
            />
            <Input
              type="number"
              label="익절 (%)"
              value={settings.takeProfit}
              onChange={(value) => setSettings({...settings, takeProfit: Number(value)})}
              placeholder="2"
            />
            <Input
              type="number"
              label="손절 (%)"
              value={settings.stopLoss}
              onChange={(value) => setSettings({...settings, stopLoss: Number(value)})}
              placeholder="2"
            />
          </div>
        </div>
        
        <Dropdown
          label="지표 선택"
          value={settings.indicator}
          onChange={(value) => setSettings({ ...settings, indicator: value })}
          options={INDICATOR_OPTIONS}
        />
        
        <div className="flex gap-4 pt-4">
          <Button onClick={handleSave} disabled={isLoading}>
            {isLoading ? '저장 중...' : isSettingsSaved ? '설정 저장됨' : '설정 저장'}
          </Button>
          <Button
            onClick={toggleAutoTrading}
            variant={isRunning ? 'danger' : 'primary'}
            disabled={serverStatus !== 'connected'}
          >
            {isRunning ? '자동매매 중지' : '자동매매 시작'}
          </Button>
        </div>
        
        {/* 테스트용 버튼들 */}
        <div className="flex gap-2 pt-2">
          <button
            type="button"
            onClick={handleTestLongPosition}
            disabled={!isSettingsSaved}
            className={`px-4 py-2 rounded-lg font-semibold transition-all duration-200 bg-blue-600 hover:bg-blue-700 text-white text-sm ${
              !isSettingsSaved ? 'opacity-50 cursor-not-allowed' : ''
            }`}
          >
            🧪 리플 롱
          </button>
          
          <button
            type="button"
            onClick={handleEmergencyClose}
            disabled={!isSettingsSaved}
            className={`px-4 py-2 rounded-lg font-semibold transition-all duration-200 bg-orange-600 hover:bg-orange-700 text-white text-sm ${
              !isSettingsSaved ? 'opacity-50 cursor-not-allowed' : ''
            }`}
          >
            🚨 긴급청산
          </button>
        </div>
        
        {/* 현재 상태 표시 */}
        <div className="mt-4 p-3 bg-gray-800 rounded-lg">
          <p className="text-sm text-gray-400">현재 상태</p>
          <p className={`text-sm font-semibold ${isRunning ? 'text-green-500' : 'text-red-500'}`}>
            {isRunning ? '자동매매 활성화' : '자동매매 비활성화'}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            선택된 지표: {INDICATOR_OPTIONS.find(i => i.value === settings.indicator)?.label}
          </p>
        </div>
      </div>
    </Card>
  );
}