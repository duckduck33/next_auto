'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Card from '../../components/common/Card';
import Input from '../../components/common/Input';
import Button from '../../components/common/Button';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();

  useEffect(() => {
    // 이미 로그인된 상태면 메인 페이지로 이동
    const isLoggedIn = localStorage.getItem('isLoggedIn');
    if (isLoggedIn === 'true') {
      router.push('/');
    }
  }, [router]);

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      // 이메일 형식 검증
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(email.trim())) {
        setError('올바른 이메일 형식을 입력해주세요.');
        return;
      }

      if (password.trim() === '') {
        setError('비밀번호를 입력해주세요.');
        return;
      }

      // 백엔드 API로 로그인 요청
      const response = await fetch('http://localhost:8000/api/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email.trim(),
          password: password
        })
      });

      const data = await response.json();

      if (response.ok && data.success) {
        // 로그인 성공 시 로컬 스토리지에 저장
        localStorage.setItem('isLoggedIn', 'true');
        localStorage.setItem('userEmail', email.trim());
        localStorage.setItem('loginTime', new Date().toISOString());

        // 메인 페이지로 이동
        router.push('/dashboard');
      } else {
        setError(data.detail || '로그인에 실패했습니다.');
      }
    } catch (error) {
      setError('로그인 중 오류가 발생했습니다.');
      console.error('로그인 오류:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async () => {
    // 이메일 형식 검증
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email.trim())) {
      setError('올바른 이메일 형식을 입력해주세요.');
      return;
    }

    if (password.trim() === '') {
      setError('비밀번호를 입력해주세요.');
      return;
    }

    try {
      // 백엔드 API로 회원가입 요청
      const response = await fetch('http://localhost:8000/api/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email.trim(),
          password: password
        })
      });

      const data = await response.json();

      if (response.ok && data.success) {
        alert('회원가입이 완료되었습니다. 로그인해주세요.');
        setPassword('');
        setError('');
      } else {
        setError(data.detail || '회원가입에 실패했습니다.');
      }
    } catch (error) {
      setError('회원가입 중 오류가 발생했습니다.');
      console.error('회원가입 오류:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <div className="w-full max-w-md">
        <Card title="자동매매 플랫폼 로그인">
          <form onSubmit={handleLogin} className="space-y-4">
            <Input
              type="email"
              label="이메일"
              value={email}
              onChange={(value) => setEmail(value)}
              placeholder="이메일을 입력하세요"
            />
            
            <Input
              type="password"
              label="비밀번호"
              value={password}
              onChange={(value) => setPassword(value)}
              placeholder="비밀번호를 입력하세요"
            />

            {error && (
              <div className="p-3 bg-red-900 text-red-200 rounded-lg text-sm">
                {error}
              </div>
            )}

            <div className="flex gap-4 pt-4">
              <Button 
                type="submit" 
                disabled={isLoading}
                className="flex-1"
              >
                {isLoading ? '로그인 중...' : '로그인'}
              </Button>
              
              <Button 
                type="button"
                onClick={handleRegister}
                variant="secondary"
                className="flex-1"
              >
                회원가입
              </Button>
            </div>
          </form>

          <div className="mt-6 p-3 bg-gray-800 rounded-lg">
            <p className="text-xs text-gray-400 text-center">
              💡 처음 사용하시는 경우 회원가입을 먼저 진행해주세요.
            </p>
          </div>
        </Card>
      </div>
    </div>
  );
}
