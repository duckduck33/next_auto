'use client';

import React, { useState, useEffect } from 'react';
import Card from './common/Card';

export default function ProfitMonitor({ sessionId, isAutoTradingEnabled }) {
  const [tradingInfo, setTradingInfo] = useState({
    initialBalance: 0,
    currentBalance: 0,
    hasPosition: false,
    positionSide: '',
    positionSize: 0,
    entryPrice: 0,
    profitRate: 0
  });

  useEffect(() => {
    if (isAutoTradingEnabled && sessionId) {
      fetchTradingInfo();
      // 5초마다 업데이트
      const interval = setInterval(fetchTradingInfo, 5000);
      return () => clearInterval(interval);
    }
  }, [isAutoTradingEnabled, sessionId]);

  const fetchTradingInfo = async () => {
    try {
      const response = await fetch('/api/profit/XRP-USDT', {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setTradingInfo(data);
      }
    } catch (error) {
      console.error('거래 정보 조회 실패:', error);
    }
  };

  return (
    <Card title="자동매매 상태">
      <div className="space-y-4">
        {/* 서버 상태 표시 */}
        <div className={`p-3 rounded-lg text-sm ${
          sessionId ? 'bg-green-900 text-green-200' : 'bg-gray-700 text-gray-300'
        }`}>
          {sessionId ? '✅ 세션 연결됨' : '⏳ 세션 대기 중'}
        </div>
        
        {/* 자동매매 상태 */}
        <div className={`p-3 rounded-lg text-sm ${
          isAutoTradingEnabled ? 'bg-blue-900 text-blue-200' : 'bg-gray-700 text-gray-300'
        }`}>
          {isAutoTradingEnabled ? '🟢 자동매매 활성화' : '🔴 자동매매 비활성화'}
        </div>

        {/* 거래 정보 */}
        {isAutoTradingEnabled && (
          <div className="space-y-3">
            <div className="p-3 bg-gray-800 rounded-lg">
              <p className="text-sm text-gray-400 mb-2">자산 정보</p>
              <div className="text-xs text-gray-500 space-y-1">
                <p>초기자산: {tradingInfo.initialBalance?.toLocaleString()} VST</p>
                <p>현재자산: {tradingInfo.currentBalance?.toLocaleString()} VST</p>
                <p className={`font-semibold ${tradingInfo.profitRate >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  수익률: {tradingInfo.profitRate?.toFixed(2)}%
                </p>
              </div>
            </div>

            <div className="p-3 bg-gray-800 rounded-lg">
              <p className="text-sm text-gray-400 mb-2">포지션 정보</p>
              <div className="text-xs text-gray-500 space-y-1">
                <p>포지션: {tradingInfo.hasPosition ? '진입' : '미진입'}</p>
                {tradingInfo.hasPosition && (
                  <>
                    <p>방향: {tradingInfo.positionSide}</p>
                    <p>수량: {tradingInfo.positionSize}</p>
                    <p>진입가격: {tradingInfo.entryPrice?.toLocaleString()}</p>
                  </>
                )}
              </div>
            </div>
          </div>
        )}

        {/* 웹훅 URL 정보 */}
        <div className="p-3 bg-gray-800 rounded-lg">
          <p className="text-sm text-gray-400">웹훅 URL</p>
          <p className="text-xs text-gray-500 mt-1 break-all">
            /api/webhook
          </p>
        </div>

        {/* 사용 안내 */}
        <div className="p-3 bg-gray-800 rounded-lg">
          <p className="text-sm text-gray-400 mb-2">사용 방법</p>
          <ol className="text-xs text-gray-500 space-y-1">
            <li>1. API 키와 시크릿 키를 입력하세요</li>
            <li>2. 거래소를 선택하고 설정을 저장하세요</li>
            <li>3. 자동매매를 시작하세요</li>
          </ol>
        </div>
      </div>
    </Card>
  );
}