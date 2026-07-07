import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';

import { VoteRecordedComponent } from './already-voted';

describe('VoteRecordedComponent', () => {
  let component: VoteRecordedComponent;
  let fixture: ComponentFixture<VoteRecordedComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VoteRecordedComponent, RouterTestingModule],
    }).compileComponents();

    fixture = TestBed.createComponent(VoteRecordedComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
