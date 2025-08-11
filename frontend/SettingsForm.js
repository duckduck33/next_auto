'use client';

import React, { useState, useEffect } from 'react';
import Card from '../common/Card';
import Input from '../common/Input';
import Button from '../common/Button';
import Dropdown from '../common/Dropdown';

// 하드코딩된 심볼을 상수로 통합관리
const HARDCODED_SYMBOL = 'XRP-USDT';
const BACKEND_URL = 'https://146.56.98.210:443';

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

export default function SettingsForm({ onSettingsChange }) {
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
      // 설정이 저장되어 있으면 저장됨 상태로 설정
      setIsSettingsSaved(true);
      
      // 백엔드에 설정 다시 전송 (새로고침 후 복구)
      if (parsedSettings.apiKey && parsedSettings.secretKey) {
        sendSettingsToBackend(parsedSettings, savedStatus ? JSON.parse(savedStatus) : false);
      }
    }
    if (savedStatus) {
      setIsRunning(JSON.parse(savedStatus));
    }

    // 백엔드 서버 상태 확인
    checkServerStatus();
  }, []);

  // 백엔드에 설정 전송하는 함수
  const sendSettingsToBackend = async (settings, isRunning) => {
    try {
      const requestBody = {
        ...settings,
        investment: parseFloat(settings.investment),
        leverage: parseInt(settings.leverage),
        takeProfit: parseFloat(settings.takeProfit),
        stopLoss: parseFloat(settings.stopLoss),
        isAutoTradingEnabled: isRunning
      };
      
      const response = await fetch(`${BACKEND_URL}/api/update-settings`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(requestBody)
      });
      
      if (response.ok) {
        console.log('설정 복구 성공');
      } else {
        console.error('설정 복구 실패:', response.status);
      }
    } catch (error) {
      console.error('설정 복구 중 오류:', error);
    }
  };

  const checkServerStatus = async () => {
    try {
      console.log('서버 상태 확인 중:', `${BACKEND_URL}/api/settings`);
      const response = await fetch(`${BACKEND_URL}/api/settings`);
      console.log('서버 응답:', response.status, response.statusText);
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
      
      const requestBody = {
        ...settings,
        investment: parseFloat(settings.investment),
        leverage: parseInt(settings.leverage),
        takeProfit: parseFloat(settings.takeProfit),
        stopLoss: parseFloat(settings.stopLoss),
        isAutoTradingEnabled: isRunning
      };
      
      console.log('설정 저장 요청:', `${BACKEND_URL}/api/update-settings`, requestBody);
      console.log('요청 헤더:', { 'Content-Type': 'application/json' });
      
      // 백엔드로 설정 전송
      const response = await fetch(`${BACKEND_URL}/api/update-settings`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(requestBody)
      });
      
      console.log('설정 저장 응답:', response.status, response.statusText);
      console.log('응답 헤더:', Object.fromEntries(response.headers.entries()));
      
      if (response.ok) {
        const responseData = await response.json();
        console.log('설정 저장 성공:', responseData);
        alert('설정이 저장되었습니다. 이제 모든 기능이 활성화됩니다.');
        
        // 설정 저장 성공 상태로 변경
        setIsSettingsSaved(true);
        
        // 설정 저장 성공 후 자동매매 상태 업데이트 제거
        // if (isRunning) {
        //   await toggleAutoTrading();
        // }
      } else {
        const errorText = await response.text();
        console.error('백엔드 설정 저장 실패:', response.status, errorText);
        alert(`설정 저장 중 오류가 발생했습니다. (${response.status})`);
      }
    } catch (error) {
      console.error('설정 저장 중 오류:', error);
      console.error('에러 타입:', error.name);
      console.error('에러 메시지:', error.message);
      console.error('에러 스택:', error.stack);
      alert(`설정 저장 중 오류가 발생했습니다: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleAutoTrading = async () => {
    const newStatus = !isRunning;
    
    // 자동매매 시작 시 포지션 확인
    if (!isRunning && newStatus) {
      try {
        // XRP-USDT로 하드코딩하여 포지션 확인
        const checkResponse = await fetch(`${BACKEND_URL}/api/check-position`);
        const checkData = await checkResponse.json();
        
        if (!checkResponse.ok) {
          alert('포지션 확인 중 오류가 발생했습니다.');
          return;
        }
        
        // 포지션이 있으면 알림
        if (checkData.hasPosition) {
          alert(`현재 ${checkData.symbol} 포지션이 있습니다. 자동매매를 시작합니다.`);
        } else {
          alert('활성 포지션이 없습니다. 자동매매를 시작합니다.');
        }
      } catch (error) {
        console.error('포지션 확인 중 오류:', error);
        alert('포지션 확인 중 오류가 발생했습니다.');
        return;
      }
    }
    
    // 자동매매 중지 시 포지션 확인 및 종료
    if (isRunning && !newStatus) {
      try {
        // 먼저 포지션 유무 확인
        const checkResponse = await fetch(`${BACKEND_URL}/api/check-position`);
        const checkData = await checkResponse.json();
        
        if (!checkResponse.ok) {
          alert('포지션 확인 중 오류가 발생했습니다.');
          return;
        }
        
        // 포지션이 있는 경우에만 종료 확인
        if (checkData.hasPosition) {
          const confirmClose = confirm(`현재 ${checkData.symbol} 포지션이 있습니다. 자동매매를 중지하면 포지션이 종료됩니다. 계속하시겠습니까?`);
          if (!confirmClose) {
            return;
          }
          
          // 포지션 종료 API 호출
          const closeResponse = await fetch(`${BACKEND_URL}/api/close-position`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol: HARDCODED_SYMBOL })  // XRP-USDT로 하드코딩
          });
          
          if (closeResponse.ok) {
            alert('포지션이 종료되었습니다.');
          } else {
            const errorData = await closeResponse.json();
            alert(`포지션 종료 실패: ${errorData.detail || '알 수 없는 오류'}`);
            return;
          }
        } else {
          // 포지션이 없는 경우 바로 중지
          alert('활성 포지션이 없습니다. 자동매매를 중지합니다.');
        }
      } catch (error) {
        console.error('포지션 확인/종료 중 오류:', error);
        alert('포지션 확인 중 오류가 발생했습니다.');
        return;
      }
    }
    
    // 백엔드에 자동매매 상태 업데이트
    try {
      const response = await fetch(`${BACKEND_URL}/api/update-settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...settings,
          investment: parseFloat(settings.investment),
          leverage: parseInt(settings.leverage),
          takeProfit: parseFloat(settings.takeProfit),
          stopLoss: parseFloat(settings.stopLoss),
          isAutoTradingEnabled: newStatus
        })
      });
      
      if (!response.ok) {
        console.error('자동매매 상태 업데이트 실패:', response.status);
        alert('자동매매 상태 업데이트 중 오류가 발생했습니다.');
        return;
      } else {
        // 성공한 경우에만 상태 변경
        setIsRunning(newStatus);
        localStorage.setItem('tvAutoStatus', JSON.stringify(newStatus));
        alert(newStatus ? '자동매매가 활성화되었습니다.' : '자동매매가 비활성화되었습니다.');
      }
    } catch (error) {
      console.error('자동매매 상태 업데이트 중 오류:', error);
      alert('자동매매 상태 업데이트 중 오류가 발생했습니다.');
    }
  };

  const handleEmergencyClose = async () => {
    if (serverStatus !== 'connected') {
      alert('백엔드 서버에 연결되지 않았습니다.');
      return;
    }

    try {
      // 먼저 수익률 API로 현재 포지션 정보 확인
      const profitResponse = await fetch(`${BACKEND_URL}/api/profit/${HARDCODED_SYMBOL}`);
      
      if (!profitResponse.ok) {
        alert('포지션 정보를 가져올 수 없습니다.');
        return;
      }
      
      const profitData = await profitResponse.json();
      
      if (!profitData || profitData.length === 0) {
        alert('활성 포지션이 없습니다.');
        return;
      }
      
      // 포지션 정보에서 심볼 추출
      const symbol = profitData[0].symbol || HARDCODED_SYMBOL;
      
      // 포지션 종료 API 호출
      const response = await fetch(`${BACKEND_URL}/api/close-position`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol: symbol })
      });

      if (response.ok) {
        alert('긴급 포지션 청산이 완료되었습니다. 자동매매는 계속 활성화됩니다.');
        // 포지션만 청산하고 자동매매 상태는 유지
        // setIsRunning(false); // 제거
        // localStorage.setItem('tvAutoStatus', JSON.stringify(false)); // 제거
        
        // 백엔드에 자동매매 상태는 그대로 유지
        const updateResponse = await fetch(`${BACKEND_URL}/api/update-settings`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            ...settings,
            investment: parseFloat(settings.investment),
            leverage: parseInt(settings.leverage),
            takeProfit: parseFloat(settings.takeProfit),
            stopLoss: parseFloat(settings.stopLoss),
            isAutoTradingEnabled: isRunning // 현재 상태 유지
          })
        });
        
        if (updateResponse.ok) {
          console.log('긴급 포지션 청산 완료. 자동매매 상태 유지.');
        } else {
          console.error('설정 업데이트 실패');
        }
      } else {
        const errorData = await response.json();
        alert(`긴급 포지션 청산 실패: ${errorData.detail || '알 수 없는 오류'}`);
      }
    } catch (error) {
      console.error('긴급 포지션 청산 중 오류:', error);
      alert('긴급 포지션 청산 중 오류가 발생했습니다.');
    }
  };

  return (
    <Card title={
      <div className="flex items-center justify-between">
        <span>빙엑스 트레이딩뷰 자동매매 설정</span>
        <a
          href="https://bingx.com/invite/ISUIKEF6/"
          target="_blank"
          rel="noopener noreferrer"
          className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors"
        >
          빙엑스 거래소 바로가기
        </a>
      </div>
    }>
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
          onChange={(value) => setSettings({ ...settings, leverage: value })}
        />
        <Input
          type="number"
          label="익절 (%)"
          value={settings.takeProfit}
          onChange={(value) => setSettings({ ...settings, takeProfit: value })}
        />
        <Input
          type="number"
          label="손절 (%)"
          value={settings.stopLoss}
          onChange={(value) => setSettings({ ...settings, stopLoss: value })}
        />
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
          <Button
            onClick={handleEmergencyClose}
            variant="danger"
            disabled={serverStatus !== 'connected'}
            className="bg-red-700 hover:bg-red-800 border-red-600"
          >
            🚨 긴급 포지션 청산
          </Button>
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
          <p className="text-xs text-gray-500 mt-1">
            웹훅 URL: {BACKEND_URL}/api/webhook
          </p>
          <p className="text-xs text-gray-400 mt-1">
            (BACKEND_URL: {BACKEND_URL})
          </p>
        </div>
      </div>
    </Card>
  );
}