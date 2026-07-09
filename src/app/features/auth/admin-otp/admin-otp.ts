import { ChangeDetectorRef, Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { RouterModule } from '@angular/router';
import { ApiService } from '../../../core/services/api';

@Component({
  selector: 'app-admin-otp',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule],
  templateUrl: './admin-otp.html',
  styleUrls: ['./admin-otp.css']
})
export class AdminOtpComponent implements OnInit, OnDestroy {
  
  otpForm!: FormGroup;
  messages: string[] = [];
  
  // Timer state
  secondsLeft: number = 120;
  private timerInterval: any;
  private readonly otpLifetimeSeconds = 120;

  constructor(
    private fb: FormBuilder,
    private router: Router,
    private api: ApiService,
    private cdr: ChangeDetectorRef
  ) { }

  ngOnInit(): void {
    // Initialize form with required validation and exactly 6 digits
    this.otpForm = this.fb.group({
      otp: ['', [Validators.required, Validators.pattern('^[0-9]{6}$')]]
    });

    this.startTimer();
  }

  ngOnDestroy(): void {
    // Prevent memory leaks by clearing the interval when the component is destroyed
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
    }
  }

  startTimer(): void {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
    }

    this.secondsLeft = this.otpLifetimeSeconds;
    this.otpForm.get('otp')?.enable();

    this.timerInterval = setInterval(() => {
      if (this.secondsLeft > 0) {
        this.secondsLeft--;
      } else {
        clearInterval(this.timerInterval);
        this.timerInterval = null;
        this.messages = ['Your OTP has expired. Please request a new one.'];
        this.otpForm.get('otp')?.disable();
      }
      this.cdr.detectChanges();
    }, 1000);
  }

  resendOtp(): void {
    this.api.adminOtp({ resend: true }).subscribe({
      next: (res: any) => {
        this.messages = res?.fallback_otp
          ? [`A new code has been sent.`]
          : ['A new code has been sent to your email.'];
        this.otpForm.get('otp')?.enable();
        this.otpForm.reset();
        this.startTimer();
      },
      error: err => {
        const msg = err?.error?.error || 'Unable to resend OTP.';
        this.messages = [msg];
      }
    });
  }

  onSubmit(): void {
    if (!this.otpForm.valid || this.secondsLeft <= 0) {
      this.messages = ['Please enter a valid 6-digit code.'];
      return;
    }

    const otpValue = this.otpForm.value.otp;
    this.api.adminOtp({ otp: otpValue }).subscribe({
      next: () => this.router.navigate(['/admin-dashboard']),
      error: err => {
        const msg = err?.error?.error || 'Invalid OTP. Please try again.';
        this.messages = [msg];
      }
    });
  }

}
