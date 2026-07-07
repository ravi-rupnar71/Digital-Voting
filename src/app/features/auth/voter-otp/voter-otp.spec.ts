import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';

import { VoterOtpComponent } from './voter-otp';

describe('VoterOtpComponent', () => {
  let component: VoterOtpComponent;
  let fixture: ComponentFixture<VoterOtpComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VoterOtpComponent, RouterTestingModule],
    }).compileComponents();

    fixture = TestBed.createComponent(VoterOtpComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
