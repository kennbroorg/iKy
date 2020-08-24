import { ChangeDetectionStrategy, Component, OnInit, OnDestroy, ViewChild, ElementRef, TemplateRef } from '@angular/core';
import { NbThemeService } from '@nebular/theme';
import { DomSanitizer, SafeUrl } from '@angular/platform-browser';

// Search
import { NbSearchService } from '@nebular/theme';

// RxJS
import { takeWhile } from 'rxjs/operators' ;
import { Observable } from 'rxjs/Observable';
import { mergeMap } from 'rxjs/operators';

// Toaster 
import { ToasterConfig } from 'angular2-toaster';
import 'style-loader!angular2-toaster/toaster.css';
import { NbGlobalLogicalPosition, NbGlobalPhysicalPosition, NbGlobalPosition, NbToastrService } from '@nebular/theme';
import { NbDialogService } from '@nebular/theme';

// Data Service
import { DataGatherInfoService } from '../../@core/data/data-gather-info.service';

@Component({
    selector: 'ngx-comparison',
    styleUrls: ['./comparison.component.scss'],
    templateUrl: './comparison.component.html',
    changeDetection: ChangeDetectionStrategy.Default
})

export class ComparisonComponent implements OnInit {
    @ViewChild('pageComparison', { static: false }) private nbCardContainer: ElementRef;
    @ViewChild('dialogComparisonError', { static: false }) private dialog: TemplateRef<any>;
    public  comparison: any = [];
    public  datas: any;
    public  flippedCal: any;
    public  searchSubs: any;

    public  validationShow = {
        hard: true,
        soft: true,
        no: true,
    };

    public  flipped = false;


    constructor(private searchService: NbSearchService, 
                private sanitizer: DomSanitizer,
                private dialogService: NbDialogService,    
                private dataGatherService: DataGatherInfoService) {
    }

    ngOnInit() {

        console.log("ComparisonComponent ngOnInit")
        // Check global data
        this.comparison = this.dataGatherService.pullGather();
        console.log("ComparisonComponent ngOnInit", this.comparison)
        if (this.comparison['data_comp']) {
            this.flippedCal = true;
        } else {
            this.flippedCal = false;
        }
        console.log("data_comp",this.comparison['data_comp'])
        console.log("flip",this.flippedCal)
    }

    formatDate(date) {
        let day = date.getDate()
        let month = date.getMonth() + 1
        let year = String(date.getFullYear())

        if (month < 10) { month = "0" + String(month)}
        if (day < 10) { day = "0" + String(day)}
         
        return (`${year}-${month}-${day}`)
    }

    toggleFlipViewAndSearch(twitterf, calf, twitters, cals) {
        console.log("Comparison Time");
        console.log("twitterf", twitterf);
        console.log("calf", calf);
        console.log("twitters", twitters);
        console.log("cals", cals);

        let datef_from_string = calf.split(" - ")[0];
        let datef_to_string = calf.split(" - ")[1];
        let dates_from_string = cals.split(" - ")[0];
        let dates_to_string = cals.split(" - ")[1];

        if (twitterf == '') {
          this.openDialogError("The twitter account must be entered");
        } else if (isNaN(Date.parse(datef_from_string)) || isNaN(Date.parse(datef_to_string))) {
          this.openDialogError("The first date range must be entered");
        } else if (twitters != '' && (isNaN(Date.parse(dates_from_string)) || isNaN(Date.parse(dates_to_string)))) {
          this.openDialogError("The second date range must be entered");
        } else {
            let datef_from = new Date(datef_from_string);
            let datef_to = new Date(datef_to_string);
            let dates_from = new Date(dates_from_string);
            let dates_to = new Date(dates_to_string);

            console.log("datef_from", datef_from);
            console.log("datef_to", datef_to);
            console.log("dates_from", dates_from);
            console.log("dates_to", dates_to);
 
            this.flippedCal = !this.flippedCal;

            // JSON datas
            this.datas = {
                twitterf: twitterf, 
                datef_from: this.formatDate(datef_from),
                datef_to: this.formatDate(datef_to),
                twitters: twitters, 
                dates_from: this.formatDate(dates_from),
                dates_to: this.formatDate(dates_to),
                flippedCal: this.flippedCal,
            };

            console.log("Datas", this.datas);
            this.dataGatherService.pushGather('data_comp', this.datas);
            
            // this.gathered = this.dataGatherService.initialize();
            // console.log("Global data initialize (Advance Gatherer)", this.gathered);

            this.comparison = this.dataGatherService.gathererComparison(this.datas); 
            this.comparison = this.dataGatherService.pullGather();
        }
    }

    toggleFlipView() {
        console.log("Flipped Prev", this.flippedCal);
        this.flippedCal = !this.flippedCal;
        console.log("Flipped After", this.flippedCal);
        this.dataGatherService.removeGather("data_comp");
        this.dataGatherService.removeGather("twitter_infof");
        this.dataGatherService.removeGather("twitter_infos");
        this.dataGatherService.removeGather("twitter_compf");
        this.dataGatherService.removeGather("twitter_comps");
        console.log(this.comparison)
    }

    //openDialogError(dialog: TemplateRef<any>) {
    openDialogError(text) {
        this.dialogService.open(this.dialog, 
            { context: text });
    }
}
