import React, { useState, useEffect, useRef } from 'react';
import { X, Mail, Phone, Lock, ArrowLeft, ShieldCheck, RefreshCw, CheckCircle2, AlertCircle } from 'lucide-react';
import { sendOtp, verifyOtp } from '../services/api';

const COUNTRY_CODES = [
  { code: '+91', country: 'India 🇮🇳' },
  { code: '+1', country: 'USA / Canada 🇺🇸 🇨🇦' },
  { code: '+44', country: 'United Kingdom 🇬🇧' },
  { code: '+971', country: 'UAE 🇦🇪' },
  { code: '+61', country: 'Australia 🇦🇺' },
  { code: '+65', country: 'Singapore 🇸🇬' },
  { code: '+49', country: 'Germany 🇩🇪' },
  { code: '+33', country: 'France 🇫🇷' },
  { code: '+81', country: 'Japan 🇯🇵' },
];

export default function AuthModal({ isOpen, onClose, onAuthSuccess, promptMessage }) {
  const [authType, setAuthType] = useState('email'); // 'email' | 'phone'
  const [emailInput, setEmailInput] = useState('');
  const [phoneInput, setPhoneInput] = useState('');
  const [countryCode, setCountryCode] = useState('+91');

  // Step state: 'input' | 'otp'
  const [step, setStep] = useState('input');

  // OTP Digits state array
  const [otpDigits, setOtpDigits] = useState(['', '', '', '', '', '']);
  const digitRefs = useRef([]);

  // Timer & Loading states
  const [countdown, setCountdown] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Reset state when modal opens/closes
  useEffect(() => {
    if (!isOpen) {
      setStep('input');
      setOtpDigits(['', '', '', '', '', '']);
      setErrorMsg('');
      setSuccessMsg('');
      setIsLoading(false);
      setCountdown(0);
    }
  }, [isOpen]);

  // Countdown Timer
  useEffect(() => {
    let timer;
    if (countdown > 0) {
      timer = setInterval(() => {
        setCountdown((prev) => prev - 1);
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [countdown]);

  if (!isOpen) return null;

  const currentIdentifier = authType === 'email' ? emailInput.trim() : phoneInput.trim();

  // Validate Input
  const isValidInput = () => {
    if (authType === 'email') {
      return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailInput.trim());
    } else {
      const cleanDigits = phoneInput.replace(/[^\d]/g, '');
      return cleanDigits.length >= 8 && cleanDigits.length <= 15;
    }
  };

  // Step 1: Send OTP
  const handleSendOtp = async (e) => {
    if (e) e.preventDefault();
    if (!isValidInput() || isLoading) return;

    setIsLoading(true);
    setErrorMsg('');
    setSuccessMsg('');

    try {
      const res = await sendOtp(currentIdentifier, authType, countryCode);
      setStep('otp');
      setCountdown(60);
      setSuccessMsg(res.message || `Verification code sent to ${currentIdentifier}`);
      // Auto-focus first OTP digit input box after step transition
      setTimeout(() => {
        if (digitRefs.current[0]) digitRefs.current[0].focus();
      }, 100);
    } catch (err) {
      setErrorMsg(err.message || 'Failed to send OTP verification code.');
    } finally {
      setIsLoading(false);
    }
  };

  // Handle 6-Digit OTP Box Entry
  const handleDigitChange = (index, value) => {
    if (!/^\d*$/.test(value)) return;

    const newDigits = [...otpDigits];
    // Take last entered character if multiple typed
    newDigits[index] = value.slice(-1);
    setOtpDigits(newDigits);
    setErrorMsg('');

    // Auto-advance focus to next digit box
    if (value && index < 5) {
      if (digitRefs.current[index + 1]) {
        digitRefs.current[index + 1].focus();
      }
    }

    // Auto-trigger verification if all 6 digits completed
    const fullOtp = newDigits.join('');
    if (fullOtp.length === 6 && !newDigits.includes('')) {
      handleVerifyOtp(fullOtp);
    }
  };

  // Handle Backspace Navigation in OTP Boxes
  const handleDigitKeyDown = (index, e) => {
    if (e.key === 'Backspace') {
      if (!otpDigits[index] && index > 0) {
        if (digitRefs.current[index - 1]) {
          digitRefs.current[index - 1].focus();
        }
      }
    }
  };

  // Handle Paste Event in OTP Boxes
  const handleOtpPaste = (e) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').replace(/[^\d]/g, '').slice(0, 6);
    if (pastedData) {
      const digitsArr = pastedData.split('');
      const newDigits = ['', '', '', '', '', ''];
      digitsArr.forEach((d, i) => {
        if (i < 6) newDigits[i] = d;
      });
      setOtpDigits(newDigits);
      setErrorMsg('');

      // Focus last filled box
      const lastIndex = Math.min(digitsArr.length - 1, 5);
      if (digitRefs.current[lastIndex]) {
        digitRefs.current[lastIndex].focus();
      }

      if (pastedData.length === 6) {
        handleVerifyOtp(pastedData);
      }
    }
  };

  // Step 2: Verify OTP
  const handleVerifyOtp = async (codeToVerify) => {
    const finalCode = codeToVerify || otpDigits.join('');
    if (finalCode.length !== 6 || isLoading) return;

    setIsLoading(true);
    setErrorMsg('');

    try {
      const res = await verifyOtp(currentIdentifier, authType, finalCode, countryCode);
      setSuccessMsg('Account verified successfully!');
      setTimeout(() => {
        onAuthSuccess && onAuthSuccess(res.user);
        onClose();
      }, 500);
    } catch (err) {
      setErrorMsg(err.message || 'Invalid or expired verification code.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content glass-card auth-modal-content" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <div className="modal-title">
            <Lock size={18} className="gold-text" />
            <span>{step === 'input' ? 'Account Authentication' : 'Verify OTP Code'}</span>
          </div>
          <button className="close-btn" onClick={onClose}><X size={18} /></button>
        </div>

        {/* Modal Body */}
        <div className="modal-body auth-modal-body">
          {/* Prompt banner if user accessed protected feature */}
          {promptMessage && step === 'input' && (
            <div className="auth-prompt-banner">
              <ShieldCheck size={16} />
              <span>{promptMessage}</span>
            </div>
          )}

          {/* Feedback Banners */}
          {errorMsg && (
            <div className="auth-status-banner error">
              <AlertCircle size={16} />
              <span>{errorMsg}</span>
            </div>
          )}

          {successMsg && (
            <div className="auth-status-banner success">
              <CheckCircle2 size={16} />
              <span>{successMsg}</span>
            </div>
          )}

          {step === 'input' ? (
            /* STEP 1: Choose Email or Phone */
            <form onSubmit={handleSendOtp} className="auth-form">
              {/* Authentication Mode Toggle Tabs */}
              <div className="auth-type-tabs">
                <button
                  type="button"
                  className={`auth-tab-btn ${authType === 'email' ? 'active' : ''}`}
                  onClick={() => { setAuthType('email'); setErrorMsg(''); }}
                >
                  <Mail size={15} />
                  <span>Email</span>
                </button>

                <button
                  type="button"
                  className={`auth-tab-btn ${authType === 'phone' ? 'active' : ''}`}
                  onClick={() => { setAuthType('phone'); setErrorMsg(''); }}
                >
                  <Phone size={15} />
                  <span>Phone Number</span>
                </button>
              </div>

              {/* Input Fields */}
              {authType === 'email' ? (
                <div className="input-group">
                  <label className="input-label">Email Address</label>
                  <div className="input-wrapper">
                    <Mail size={16} className="input-icon" />
                    <input
                      type="email"
                      className="auth-input"
                      placeholder="name@example.com"
                      value={emailInput}
                      onChange={(e) => { setEmailInput(e.target.value); setErrorMsg(''); }}
                      autoFocus
                      required
                    />
                  </div>
                </div>
              ) : (
                <div className="input-group">
                  <label className="input-label">Phone Number</label>
                  <div className="phone-input-row">
                    <select
                      className="country-select"
                      value={countryCode}
                      onChange={(e) => setCountryCode(e.target.value)}
                    >
                      {COUNTRY_CODES.map((c) => (
                        <option key={c.code} value={c.code}>
                          {c.code} ({c.country})
                        </option>
                      ))}
                    </select>

                    <div className="input-wrapper flex-1">
                      <Phone size={16} className="input-icon" />
                      <input
                        type="tel"
                        className="auth-input"
                        placeholder="98765 43210"
                        value={phoneInput}
                        onChange={(e) => { setPhoneInput(e.target.value); setErrorMsg(''); }}
                        autoFocus
                        required
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Submit Button */}
              <button
                type="submit"
                className="btn-gold-pill auth-submit-btn"
                disabled={!isValidInput() || isLoading}
              >
                {isLoading ? (
                  <span className="btn-loading-row">
                    <RefreshCw size={16} className="spinning" /> Sending Code...
                  </span>
                ) : (
                  <span>Send Verification Code</span>
                )}
              </button>
            </form>
          ) : (
            /* STEP 2: 6-Digit OTP Verification Screen */
            <div className="otp-verification-wrapper">
              <div className="otp-target-info">
                <p className="otp-sent-text">
                  Enter 6-digit code sent to{' '}
                  <strong>
                    {authType === 'phone' ? `${countryCode} ${phoneInput}` : emailInput}
                  </strong>
                </p>

                <button
                  type="button"
                  className="edit-identifier-btn"
                  onClick={() => { setStep('input'); setOtpDigits(['','','','','','']); setErrorMsg(''); }}
                >
                  <ArrowLeft size={13} /> Edit {authType}
                </button>
              </div>

              {/* 6 Digit Input Boxes */}
              <div className="otp-boxes-row" onPaste={handleOtpPaste}>
                {otpDigits.map((digit, idx) => (
                  <input
                    key={idx}
                    ref={(el) => (digitRefs.current[idx] = el)}
                    type="text"
                    inputMode="numeric"
                    maxLength={1}
                    className={`otp-digit-box ${digit ? 'filled' : ''}`}
                    value={digit}
                    onChange={(e) => handleDigitChange(idx, e.target.value)}
                    onKeyDown={(e) => handleDigitKeyDown(idx, e)}
                    disabled={isLoading}
                  />
                ))}
              </div>

              {/* Countdown & Resend Option */}
              <div className="otp-actions-row">
                {countdown > 0 ? (
                  <span className="timer-text">Resend code in {countdown}s</span>
                ) : (
                  <button
                    type="button"
                    className="resend-otp-btn"
                    onClick={handleSendOtp}
                    disabled={isLoading}
                  >
                    Resend OTP Code
                  </button>
                )}
              </div>

              {/* Manual Verify Button */}
              <button
                type="button"
                className="btn-gold-pill auth-submit-btn"
                onClick={() => handleVerifyOtp()}
                disabled={otpDigits.join('').length !== 6 || isLoading}
              >
                {isLoading ? (
                  <span className="btn-loading-row">
                    <RefreshCw size={16} className="spinning" /> Verifying...
                  </span>
                ) : (
                  <span>Verify & Login</span>
                )}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
