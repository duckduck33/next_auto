'use client';

import React from 'react';
import Card from './common/Card';

const BACKEND_URL = 'http://localhost:8000';

export default function ProfitMonitor({ sessionId, isAutoTradingEnabled }) {
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

        {/* 웹훅 URL 정보 */}
        <div className="p-3 bg-gray-800 rounded-lg">
          <p className="text-sm text-gray-400">웹훅 URL</p>
          <p className="text-xs text-gray-500 mt-1 break-all">
            {BACKEND_URL}/api/webhook
                  </p>
                </div>

        {/* 사용 안내 */}
        <div className="p-3 bg-gray-800 rounded-lg">
          <p className="text-sm text-gray-400 mb-2">사용 방법</p>
          <ol className="text-xs text-gray-500 space-y-1">
            <li>1. API 키와 시크릿 키를 입력하세요</li>
            <li>2. 거래소를 선택하고 설정을 저장하세요</li>
            <li>3. 자동매매를 시작하세요</li>
            <li>4. TradingView에서 위 웹훅 URL로 신호를 보내세요</li>
          </ol>
        </div>
      </div>
    </Card>
  );
}