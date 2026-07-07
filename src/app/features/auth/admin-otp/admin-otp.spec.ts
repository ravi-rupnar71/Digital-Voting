import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AdminOtpComponent } from './admin-otp';

describe('AdminOtpComponent', () => {
  let component: AdminOtpComponent;
  let fixture: ComponentFixture<AdminOtpComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AdminOtpComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(AdminOtpComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
