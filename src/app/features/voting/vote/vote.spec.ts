import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';

import { VoteComponent } from './vote';

describe('VoteComponent', () => {
  let component: VoteComponent;
  let fixture: ComponentFixture<VoteComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VoteComponent, RouterTestingModule],
    }).compileComponents();

    fixture = TestBed.createComponent(VoteComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
