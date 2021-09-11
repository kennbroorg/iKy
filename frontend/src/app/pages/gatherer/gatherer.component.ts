import { TemplateRef,
         ChangeDetectionStrategy,
         Component,
         OnInit,
         OnDestroy,
         ViewChild,
         ElementRef } from '@angular/core';

// import { NbThemeService } from '@nebular/theme';
import { DomSanitizer, SafeUrl } from '@angular/platform-browser';
import { NbDialogService } from '@nebular/theme';

// Search
import { NbSearchService } from '@nebular/theme';

// RxJS
// import { takeWhile } from 'rxjs/operators' ;
// import { Observable } from 'rxjs/Observable';
// import { mergeMap } from 'rxjs/operators';

// Toaster
// import { ToasterConfig } from 'angular2-toaster';
// import 'style-loader!angular2-toaster/toaster.css';
// import { NbGlobalLogicalPosition,
// NbGlobalPhysicalPosition,
// NbGlobalPosition,
// NbToastrService } from '@nebular/theme';
// import { NbToastStatus } from '@nebular/theme/components/toastr/model';


// Data Service
import { DataGatherInfoService } from '../../@core/data/data-gather-info.service';

// Report
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import * as htmlToImage from 'html-to-image';
import { toPng, toJpeg, toBlob, toPixelData, toSvg } from 'html-to-image';

@Component({
    selector: 'ngx-gatherer',
    styleUrls: ['./gatherer.component.scss'],
    templateUrl: './gatherer.component.html',
    changeDetection: ChangeDetectionStrategy.Default
})

export class GathererComponent implements OnInit {
    @ViewChild('pageGather', { static: false }) private nbCardContainer: ElementRef;
    public  gathered: any = [];
    public  datas: any;
    public  processing: boolean = false;
    public  reportEnd: boolean = false;
    public  reportMessage: string;
    public  report: any;
    public  searchSubs: any;
    public  svg: any;
    public  img: any;
    public  divInvisible: any;
    public  getCanvas: any;
    public  downloadJsonHref: any;
    public  timeline: any = [];
    public  profile: any = [];
    public  name: any = [];
    public  location: any = [];
    public  gender: any = [];
    public  social: any = [];
    public  photo: any = [];
    public  organization: any = [];

    public  onH: boolean = true;
    public  onS: boolean = true;
    public  onN: boolean = true;

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
        this.searchSubs = this.searchService.onSearchSubmit()
          .subscribe((data: any) => {
            // Initialize global data
            this.gathered = this.dataGatherService.initialize();
            console.log('Global data initialize', this.gathered);

            console.log('Search', data);
            this.gathered = this.dataGatherService.validateEmail(data.term);
        });

        console.log('GathererComponent ngOnInit');
        // Check global data
        this.gathered = this.dataGatherService.pullGather();
        console.log('GathererComponent ngOnInit', this.gathered);
        console.log('GathererComponent ngOnInit length', this.jsonLength(this.gathered));
    }

    ngOnDestroy () {
        this.searchSubs.unsubscribe();
    }

    generateDownloadJsonUri() {
        let sJson = JSON.stringify(this.gathered);
        let element = document.createElement('a');
        element.setAttribute('href', 'data:text/json;charset=UTF-8,' + encodeURIComponent(sJson));
        element.setAttribute('download', 'gathered.json');
        element.style.display = 'none';
        document.body.appendChild(element);
        element.click(); // simulate click
        document.body.removeChild(element);
    }

    jsonLength(obj: any) {
        try {
          return Object.keys(obj).length;
        }
        catch(e) {
          return 0;
        }
    }

    setValidation(val: any) {
        this.validationShow[val] = !this.validationShow[val];
        console.log(this.validationShow);
    }

    checkValidation(val: any) {
        return this.validationShow[val]
    }

    toggleFlipViewAndSearch(email, username, twitter, instagram, linkedin,
                            github, tiktok, tinder, venmo, reddit, spotify, twitch) {
        console.log('Advance Search');
        console.log('email', email);
        console.log('username', username);
        console.log('twitter', twitter);
        console.log('instagram', instagram);
        console.log('linkedin', linkedin);
        console.log('github', github);
        console.log('tiktok', tiktok);
        console.log('tinder', tinder);
        console.log('venmo', venmo);
        console.log('reddit', reddit);
        console.log('spotify', spotify);
        console.log('twitch', twitch);

        this.flipped = !this.flipped;

        // JSON datas
        this.datas = {email: email,
            username: username,
            twitter: twitter,
            instagram: instagram,
            linkedin: linkedin,
            github: github,
            tiktok: tiktok,
            tinder: tinder,
            venmo: venmo,
            reddit: reddit,
            spotify: spotify,
            twitch: twitch,
        };

        this.gathered = this.dataGatherService.initialize();
        console.log('Global data initialize (Advance Gatherer)', this.gathered);

        this.gathered = this.dataGatherService.gathererInfoAdvance(this.datas);
        this.gathered = this.dataGatherService.pullGather();

    }

    toggleFlipView() {
        this.flipped = !this.flipped;
    }

    // As All Functions in js are asynchronus, to use await i am using async here
    async generateAllPdfDialog(dialog: TemplateRef<any>) {
        this.reportEnd = false;
        this.dialogService.open(
          dialog,
          {
            context: 'this is some additional data passed to dialog',
            closeOnEsc: false,
            closeOnBackdropClick: false,
          });
        this.reportMessage = 'Initializing report...'

        console.log('Report... ');

        let infoText: string;
        let moduleHeight: number;
        this.profile = [];
        this.timeline = [];
        this.name = [];
        this.location = [];
        this.gender = [];
        this.organization = [];
        this.social = [];
        this.photo = [];

        // General config
        const doc = new jsPDF('p', 'mm', 'a4');
        const pageHeight = doc.internal.pageSize.getHeight();
        const img = new Image();
        const imgBack = new Image();
        const imgiKy = new Image();
        let hl = 0;
        let svg: any;

        // Config Page
        doc.internal.events.subscribe('addPage', function() {
            const pageSize = doc.internal.pageSize;
            // Side image
            doc.setDrawColor('#1a1a1a');
            doc.setFillColor('#1a1a1a');
            doc.rect(0, 0, pageSize.width, pageSize.height, 'F');
            doc.setDrawColor('#000000');
            doc.setFillColor('#000000');
            doc.rect(0, 0, 210, 15, 'F');
            doc.rect(0, 285, 210, 15, 'F');
            img.src = 'assets/images/back1.jpg';
            doc.addImage(img, 'png', 0, 15, 95, 270);

            // doc.addImage(myimage, 'JPG', 0, 0, pageSize.width, pageSize.height);
        });

        // Page 1
        doc.setDrawColor('#1a1a1a');
        doc.setFillColor('#1a1a1a');
        doc.rect(0, 0, 210, 300, 'F');
        imgBack.src = 'assets/images/blur-bg.jpg';
        doc.addImage(imgBack, 'png', 0, 50, 210, 200);

        img.src = 'assets/images/iKy-Logo.png';
        doc.addImage(img, 'png', 60, 105, 90, 98);

        // Top Line
        doc.setLineWidth(15);
        doc.setDrawColor('#000000');
        doc.line(10, 50, 200, 50);
        doc.line(10, 250, 200, 250);

        doc.setLineWidth(3);
        doc.setDrawColor('#05fcfc');
        doc.rect(50, 105, 110, 98, 'S');

        doc.setFont('helvetica');
        doc.setFontSize(50);
        doc.setTextColor('#05fcfc');
        doc.text('REPORT', 105, 100, {align: 'center'});

        /////////////////////////////////////////////////////////////////
        // Input page
        /////////////////////////////////////////////////////////////////
        doc.addPage();
        doc.setFontSize(25);
        hl = 20;

        // Header title page
        img.src = 'assets/images/h1.jpg';
        doc.addImage(img, 'png', 100, 15, 100, 14);
        img.src = 'assets/images/iKy-Logo.png';
        doc.addImage(img, 'png', 185, 17, 10, 10);
        doc.setFontSize(12);
        doc.setTextColor('#05fcfc');
        doc.text('INPUT - Selectors', 105, 23);

        // Header title page
        // img.src = 'assets/images/h2.png';
        // doc.addImage(img, 'png', 10, 10, 190, 14);
        // img.src = 'assets/images/iKy-Logo.png';
        // doc.addImage(img, 'png', 185, 12, 10, 10);
        // doc.setFontSize(12);
        // doc.setTextColor('#05fcfc');
        // doc.text('INPUT - Selectors', 15, 18);

        let email, username, twitter, instagram, linkedin, github, tiktok;
        let tinder, venmo, reddit, spotify, twitch;
        if (this.gathered['email'] && !this.gathered['data']) {
            email = this.gathered['email'];
        } else if (this.gathered['data'] && this.gathered['data']['email'] !== '') {
            email = this.gathered['data']['email'];
        } else {
            email = '-----';
        }
        username = (this.gathered['data'] && this.gathered['data']['username']) ?
            this.gathered['data']['username'] : '-----';
        twitter = (this.gathered['data'] && this.gathered['data']['twitter']) ?
            this.gathered['data']['twitter'] : '-----';
        instagram = (this.gathered['data'] && this.gathered['data']['instagram']) ?
            this.gathered['data']['instagram'] : '-----';
        linkedin = (this.gathered['data'] && this.gathered['data']['linkedin']) ?
            this.gathered['data']['linkedin'] : '-----';
        github = (this.gathered['data'] && this.gathered['data']['github']) ?
            this.gathered['data']['github'] : '-----';
        tiktok = (this.gathered['data'] && this.gathered['data']['tiktok']) ?
            this.gathered['data']['tiktok'] : '-----';
        tinder = (this.gathered['data'] && this.gathered['data']['tinder']) ?
            this.gathered['data']['tinder'] : '-----';
        venmo = (this.gathered['data'] && this.gathered['data']['venmo']) ?
            this.gathered['data']['venmo'] : '-----';
        reddit = (this.gathered['data'] && this.gathered['data']['reddit']) ?
            this.gathered['data']['reddit'] : '-----';
        spotify = (this.gathered['data'] && this.gathered['data']['spotify']) ?
            this.gathered['data']['spotify'] : '-----';
        twitch = (this.gathered['data'] && this.gathered['data']['twitch']) ?
            this.gathered['data']['twitch'] : '-----';

        const columns = [['Selectors', 'Values']];
        const rows = [
            ['E-mail', email],
            ['Username', username],
            ['Twitter', twitter],
            ['Instagram', instagram],
            ['Linkedin', linkedin],
            ['Github', github],
            ['Tiktok', tiktok],
            ['Tinder', tinder],
            ['Venmo', venmo],
            ['Reddit', reddit],
            ['Spotify', spotify],
            ['Twitch', twitch],
        ];

        autoTable(doc, {
             head: columns,
             body: rows,
             headStyles: {fillColor: '#50fcfc',
                          cellPadding: {top: 5, right: 5, bottom: 5, left: 5},
                          lineWidth: 3,
                          halign: 'center',
                          textColor: '#000000',
                          lineColor: '#1A1A1A'},
             bodyStyles: {fillColor: '#1A1A1A',
                          cellPadding: {top: 5, right: 5, bottom: 5, left: 5},
                          lineWidth: 3,
                          textColor: '#50fcfc',
                          lineColor: '#1A1A1A'},
             columnStyles: {
                 0: {fillColor: '#393f46', cellWidth: 50},
                 1: {fillColor: '#22262a', cellWidth: 70},
             },
             margin: {top: 60, left: 45},
        });

        /////////////////////////////////////////////////////////////////
        // TaskExec
        /////////////////////////////////////////////////////////////////
        doc.addPage();
        doc.setFontSize(25);

        // Header title page
        img.src = 'assets/images/h1.jpg';
        doc.addImage(img, 'png', 100, 15, 100, 14);
        img.src = 'assets/images/iKy-Logo.png';
        doc.addImage(img, 'png', 185, 17, 10, 10);
        doc.setFontSize(12);
        doc.setTextColor('#05fcfc');
        doc.text('PROCESSES - Executed', 105, 23);

        // Get and format TaskExec
        const bodyTable = [];
        let elem = [];
        const list = this.gathered['taskexec'];

        for (const i in list) {
            if (list[i]['module']) {
                elem = [list[i]['module'],
                        list[i]['param'],
                        list[i]['from'],
                        list[i]['score'],
                        list[i]['state']];
                bodyTable.push(elem);
            }
        }

        autoTable(doc, {
             head: [['Module', 'Param', 'Exec by', 'Score', 'State']],
             body: bodyTable,
             headStyles: {fillColor: '#50fcfc',
                          cellPadding: {top: 3, right: 3, bottom: 3, left: 3},
                          lineWidth: 1,
                          halign: 'center',
                          textColor: '#000000',
                          lineColor: '#1A1A1A'},
             bodyStyles: {fillColor: '#1A1A1A',
                          cellPadding: {top: 3, right: 3, bottom: 3, left: 3},
                          lineWidth: 1,
                          textColor: '#50fcfc',
                          lineColor: '#1A1A1A'},
             columnStyles: {
                 0: {fillColor: '#393f46'},
                 1: {fillColor: '#22262a'},
                 2: {fillColor: '#393f46'},
                 3: {fillColor: '#22262a'},
                 4: {fillColor: '#393f46'},
             },
             margin: {top: 40},
        });

        /////////////////////////////////////////////////////////////////
        // EmailrepIO module report
        /////////////////////////////////////////////////////////////////
        if (this.gathered['emailrep'] &&
            this.gathered['emailrep']['result'] &&
            this.gathered['emailrep']['result'].length > 3) {

            this.reportMessage = 'EmailrepIO module...'
            // moduleHeight = 80;

            // Validate pageHeight
            // if ( hl + moduleHeight > pageHeight) {
            //     doc.addPage();
            //     hl = 20;
            // }

            let emailrep = false;

            doc.addPage();
            doc.setFontSize(25);
            hl = 40;

            // Header title page
            img.src = 'assets/images/h1.jpg';
            doc.addImage(img, 'png', 100, 15, 100, 14);
            img.src = 'assets/images/iKy-Logo.png';
            doc.addImage(img, 'png', 185, 17, 10, 10);
            doc.setFontSize(12);
            doc.setTextColor('#05fcfc');
            doc.text('MODULE - EmailRepIO', 105, 23);

            // Information table
            if (this.gathered['emailrep'] &&
                this.gathered['emailrep']['result'] &&
                this.gathered['emailrep']['result'][4] &&
                this.gathered['emailrep']['result'][4]['graphic'] &&
                this.gathered['emailrep']['result'][4]['graphic'][0] &&
                this.gathered['emailrep']['result'][4]['graphic'][0]['details'] &&
                this.gathered['emailrep']['result'][4]['graphic'][0]['details'].length > 1) {

                this.reportMessage = 'EmailrepIO module...(Details)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divEmailrepInfo');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                emailrep = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['emailrep']['result'][4]['graphic'][0]['details'];

                for (const i in list) {
                    if (list[i]['title'] !== 'EmailRep') {
                        elem = [list[i]['title'], list[i]['subtitle']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Name', 'Value']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                }
            }

            hl = hl + 10;

            // Information table
            if (this.gathered['emailrep'] &&
                this.gathered['emailrep']['result'] &&
                this.gathered['emailrep']['result'][4] &&
                this.gathered['emailrep']['result'][4]['graphic'] &&
                this.gathered['emailrep']['result'][4]['graphic'][1] &&
                this.gathered['emailrep']['result'][4]['graphic'][1]['social'] &&
                this.gathered['emailrep']['result'][4]['graphic'][1]['social'].length > 1) {

                this.reportMessage = 'EmailrepIO module...(Social)'

                svg = this.nbCardContainer.nativeElement.querySelector('#divEmailrepSocial');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                emailrep = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['emailrep']['result'][4]['graphic'][1]['social'];

                for (const i in list) {
                    if (list[i]['title'] !== 'EmailRep') {
                        elem = [list[i]['title']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Social networks']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                }
            }

            if (!emailrep) {
                doc.setLineWidth(15);
                doc.setDrawColor('#00000');
                doc.line(20, 105, 190, 105);
                doc.line(20, 155, 190, 155);
                img.src = 'assets/images/ban.png';
                doc.addImage(img, 'png', 10, 105, 190, 50);
            }

            hl = hl + 10;
        }

        /////////////////////////////////////////////////////////////////
        // Fullcontact module report
        /////////////////////////////////////////////////////////////////
        if (this.gathered['fullcontact'] &&
            this.gathered['fullcontact']['result'] &&
            this.gathered['fullcontact']['result'].length > 3) {

            this.reportMessage = 'Fullcontact module...'

            let fullcontact = false;

            doc.addPage();
            doc.setFontSize(25);
            hl = 40;

            // Header title page
            img.src = 'assets/images/h1.jpg';
            doc.addImage(img, 'png', 100, 15, 100, 14);
            img.src = 'assets/images/iKy-Logo.png';
            doc.addImage(img, 'png', 185, 17, 10, 10);
            doc.setFontSize(12);
            doc.setTextColor('#05fcfc');
            doc.text('MODULE - Fullcontact', 105, 23);

            // Information table
            if (this.gathered['fullcontact'] &&
                this.gathered['fullcontact']['result'] &&
                this.gathered['fullcontact']['result'][4] &&
                this.gathered['fullcontact']['result'][4]['graphic'] &&
                this.gathered['fullcontact']['result'][4]['graphic'][0] &&
                this.gathered['fullcontact']['result'][4]['graphic'][0]['social'] &&
                this.gathered['fullcontact']['result'][4]['graphic'][0]['social'].length > 1) {

                this.reportMessage = 'Fullcontact module...(Social)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divFullcontactGraphs');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                fullcontact = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['fullcontact']['result'][4]['graphic'][0]['social'];

                for (const i in list) {
                    if (list[i]['title'] !== 'Social') {
                        elem = [list[i]['title'], list[i]['subtitle']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Name', 'Value']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 40, left: 100},
                     startY: hl,
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                }
            }

            hl = hl + 10;

            if (!fullcontact) {
                doc.setLineWidth(15);
                doc.setDrawColor('#00000');
                doc.line(20, 105, 190, 105);
                doc.line(20, 155, 190, 155);
                img.src = 'assets/images/ban.png';
                doc.addImage(img, 'png', 10, 105, 190, 50);
            }

            hl = hl + 10;
        }

        /////////////////////////////////////////////////////////////////
        // PDL module report
        /////////////////////////////////////////////////////////////////
        if (this.gathered['peopledatalabs'] &&
            this.gathered['peopledatalabs']['result'] &&
            this.gathered['peopledatalabs']['result'].length > 3) {

            this.reportMessage = 'PeopleDataLabs module...'
            // moduleHeight = 80;

            // Validate pageHeight
            // if ( hl + moduleHeight > pageHeight) {
            //     doc.addPage();
            //     hl = 20;
            // }

            let peopledatalabs = false;

            doc.addPage();
            doc.setFontSize(25);
            hl = 40;

            // Header title page
            img.src = 'assets/images/h1.jpg';
            doc.addImage(img, 'png', 100, 15, 100, 14);
            img.src = 'assets/images/iKy-Logo.png';
            doc.addImage(img, 'png', 185, 17, 10, 10);
            doc.setFontSize(12);
            doc.setTextColor('#05fcfc');
            doc.text('MODULE - PeopleDataLabs', 105, 23);

            // Information table
            if (this.gathered['peopledatalabs'] &&
                this.gathered['peopledatalabs']['result'] &&
                this.gathered['peopledatalabs']['result'][4] &&
                this.gathered['peopledatalabs']['result'][4]['graphic'] &&
                this.gathered['peopledatalabs']['result'][4]['graphic'][0] &&
                this.gathered['peopledatalabs']['result'][4]['graphic'][0]['data'] &&
                this.gathered['peopledatalabs']['result'][4]['graphic'][0]['data'].length > 1) {

                this.reportMessage = 'PeopleDataLabs module...(Data)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divPeopledatalabsGraphs');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                peopledatalabs = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['peopledatalabs']['result'][4]['graphic'][0]['data'];

                for (const i in list) {
                    if (list[i]['title'] !== 'DataLab') {
                        elem = [list[i]['title'], list[i]['subtitle']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Name', 'Value']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Information table
            if (this.gathered['peopledatalabs'] &&
                this.gathered['peopledatalabs']['result'] &&
                this.gathered['peopledatalabs']['result'][4] &&
                this.gathered['peopledatalabs']['result'][4]['graphic'] &&
                this.gathered['peopledatalabs']['result'][4]['graphic'][1] &&
                this.gathered['peopledatalabs']['result'][4]['graphic'][1]['social'] &&
                this.gathered['peopledatalabs']['result'][4]['graphic'][1]['social'].length > 1) {

                this.reportMessage = 'Peopledatalabs module...(Social)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divPeopledatalabsSocial');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                peopledatalabs = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['peopledatalabs']['result'][4]['graphic'][1]['social'];

                for (const i in list) {
                    if (list[i]['title'] !== 'Social') {
                        elem = [list[i]['title'], list[i]['subtitle']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Social networks', 'Username']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            if (!peopledatalabs) {
                doc.setLineWidth(15);
                doc.setDrawColor('#00000');
                doc.line(20, 105, 190, 105);
                doc.line(20, 155, 190, 155);
                img.src = 'assets/images/ban.png';
                doc.addImage(img, 'png', 10, 105, 190, 50);
            }

            hl = hl + 10;
        }

        /////////////////////////////////////////////////////////////////
        // Twitter and Twint module report
        /////////////////////////////////////////////////////////////////
        if (this.gathered['twint'] &&
            this.gathered['twint']['result'] &&
            this.gathered['twint']['result'].length > 3) {

            this.reportMessage = 'Twitter (Twint) module...'
            // moduleHeight = 80;

            // Validate pageHeight
            // if ( hl + moduleHeight > pageHeight) {
            //     doc.addPage();
            //     hl = 20;
            // }

            let twint = false;

            doc.addPage();
            doc.setFontSize(25);
            hl = 40;

            // Header title page
            img.src = 'assets/images/h1.jpg';
            doc.addImage(img, 'png', 100, 15, 100, 14);
            img.src = 'assets/images/iKy-Logo.png';
            doc.addImage(img, 'png', 185, 17, 10, 10);
            doc.setFontSize(12);
            doc.setTextColor('#05fcfc');
            doc.text('MODULE - Twitter (Twint)', 105, 23);

            // Information table
            if (this.gathered['twint'] &&
                this.gathered['twint']['result'] &&
                this.gathered['twint']['result'][4] &&
                this.gathered['twint']['result'][4]['graphic'] &&
                this.gathered['twint']['result'][4]['graphic'][0] &&
                this.gathered['twint']['result'][4]['graphic'][0]['social'] &&
                this.gathered['twint']['result'][4]['graphic'][0]['social'].length > 1) {

                this.reportMessage = 'Twitter (Twint) module...(Social)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divTwintSocial');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                twint = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['twint']['result'][4]['graphic'][0]['social'];

                for (const i in list) {
                    if (list[i]['title'] !== 'DataLab') {
                        elem = [list[i]['title'], list[i]['subtitle']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Name', 'Value']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Information table
            if (this.gathered['twint'] &&
                this.gathered['twint']['result'] &&
                this.gathered['twint']['result'][4] &&
                this.gathered['twint']['result'][4]['graphic'] &&
                this.gathered['twint']['result'][4]['graphic'][2] &&
                this.gathered['twint']['result'][4]['graphic'][2]['popularity'] &&
                this.gathered['twint']['result'][4]['graphic'][2]['popularity'].length > 1) {

                this.reportMessage = 'Twitter (Twint) module...(Popularity)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divTwintPopularity');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                twint = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['twint']['result'][4]['graphic'][2]['popularity'];

                for (const i in list) {
                    if (list[i]['value'] !== 'Social') {
                        elem = [list[i]['name'], list[i]['value']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Name', 'Value']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Information table
            if (this.gathered['twint'] &&
                this.gathered['twint']['result'] &&
                this.gathered['twint']['result'][4] &&
                this.gathered['twint']['result'][4]['graphic'] &&
                this.gathered['twint']['result'][4]['graphic'][1] &&
                this.gathered['twint']['result'][4]['graphic'][1]['resume'] &&
                this.gathered['twint']['result'][4]['graphic'][1]['resume']['children'].length > 1) {

                this.reportMessage = 'Twitter (Twint) module...(Resume)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divTwintResume');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                twint = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['twint']['result'][4]['graphic'][1]['resume']['children'];
                console.log('Resume', list);

                for (const i in list) {
                    if (list[i]['value'] !== 'Social') {
                        elem = [list[i]['name'], list[i]['value']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Name', 'Value']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     // pageBreak: 'always',
                     startY: hl,
                     // didDrawPage: function (data) {
                     //     data.settings.margin.top = 40; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 65 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);
                hl = 40;
                const finalY = 40;

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Twitter (Twint)', 105, 23);
            }

            // Information table
            if (this.gathered['twint'] &&
                this.gathered['twint']['result'] &&
                this.gathered['twint']['result'][4] &&
                this.gathered['twint']['result'][4]['graphic'] &&
                this.gathered['twint']['result'][4]['graphic'][10] &&
                this.gathered['twint']['result'][4]['graphic'][10]['time'] &&
                this.gathered['twint']['result'][4]['graphic'][10]['time'].length > 1) {

                this.reportMessage = 'Twitter (Twint) module...(Timeline)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divTwintTimeline');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 25, hl, 160, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                twint = true;

                hl = hl + 55
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 65 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);
                hl = 40;
                const finalY = 40;

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Twitter (Twint)', 105, 23);
            }

            // Information table
            if (this.gathered['twint'] &&
                this.gathered['twint']['result'] &&
                this.gathered['twint']['result'][4] &&
                this.gathered['twint']['result'][4]['graphic'] &&
                this.gathered['twint']['result'][4]['graphic'][5] &&
                this.gathered['twint']['result'][4]['graphic'][5]['users'] &&
                this.gathered['twint']['result'][4]['graphic'][5]['users'].length > 1) {

                this.reportMessage = 'Twitter (Twint) module...(Users)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divTwintUsers');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                twint = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['twint']['result'][4]['graphic'][5]['users'];

                for (const i in list) {
                    if (list[i]['title'] !== 'Users') {
                        elem = [list[i]['title'], list[i]['subtitle']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Users', 'Ocurrences']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     // pageBreak: 'always',
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Validate pageHeight
            console.log(`ENTRANDO - SALTO: hl - ${hl} + 60 // pageHeight - ${pageHeight}`);
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Twitter (Twint)', 105, 23);

                hl = 40;
            }
            console.log(`SALIENDO - SALTO: hl - ${hl} + 60 // pageHeight - ${pageHeight}`);

            // Information table
            if (this.gathered['twint'] &&
                this.gathered['twint']['result'] &&
                this.gathered['twint']['result'][4] &&
                this.gathered['twint']['result'][4]['graphic'] &&
                this.gathered['twint']['result'][4]['graphic'][6] &&
                this.gathered['twint']['result'][4]['graphic'][6]['tweetslist'] &&
                this.gathered['twint']['result'][4]['graphic'][6]['tweetslist'].length > 1) {

                this.reportMessage = 'Twitter (Twint) module...(TweetList)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divTwintList');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 25, hl, 160, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                twint = true;

                hl = hl + 55
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Twitter (Twint)', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['twint'] &&
                this.gathered['twint']['result'] &&
                this.gathered['twint']['result'][4] &&
                this.gathered['twint']['result'][4]['graphic'] &&
                this.gathered['twint']['result'][4]['graphic'][4] &&
                this.gathered['twint']['result'][4]['graphic'][4]['hashtag'] &&
                this.gathered['twint']['result'][4]['graphic'][4]['hashtag'].length > 1) {

                this.reportMessage = 'Twitter (Twint) module...(Hashtag)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divTwintHashtag');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                twint = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['twint']['result'][4]['graphic'][4]['hashtag'];

                for (const i in list) {
                    if (list[i]['title'] !== 'Users') {
                        elem = [list[i]['label'], list[i]['value']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Hashtag', 'Ocurrences']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Twitter (Twint)', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['twint'] &&
                this.gathered['twint']['result'] &&
                this.gathered['twint']['result'][4] &&
                this.gathered['twint']['result'][4]['graphic'] &&
                this.gathered['twint']['result'][4]['graphic'][8] &&
                this.gathered['twint']['result'][4]['graphic'][8]['hour'] &&
                this.gathered['twint']['result'][4]['graphic'][8]['hour'].length > 1) {

                this.reportMessage = 'Twitter (Twint) module...(Hour)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divTwintHour');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 60, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                twint = true;

                hl = hl + 55;
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Twitter (Twint)', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['twint'] &&
                this.gathered['twint']['result'] &&
                this.gathered['twint']['result'][4] &&
                this.gathered['twint']['result'][4]['graphic'] &&
                this.gathered['twint']['result'][4]['graphic'][7] &&
                this.gathered['twint']['result'][4]['graphic'][7]['week'] &&
                this.gathered['twint']['result'][4]['graphic'][7]['week'].length > 1) {

                this.reportMessage = 'Twitter (Twint) module...(Week)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divTwintWeek');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 60, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                twint = true;

                hl = hl + 55;
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Twitter (Twint)', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['twitter'] &&
                this.gathered['twitter']['result'] &&
                this.gathered['twitter']['result'][4] &&
                this.gathered['twitter']['result'][4]['graphic'] &&
                this.gathered['twitter']['result'][4]['graphic'][9] &&
                this.gathered['twitter']['result'][4]['graphic'][9]['sources'] &&
                this.gathered['twitter']['result'][4]['graphic'][9]['sources'].length > 0) {

                this.reportMessage = 'Twitter (Twitter) module...(Source)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divTwitterSource');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                twint = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['twitter']['result'][4]['graphic'][9]['sources'];

                for (const i in list) {
                    if (list[i]['title'] !== 'Users') {
                        elem = [list[i]['name'], list[i]['value']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Source', 'Qty']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Twitter (Twint)', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['twitter'] &&
                this.gathered['twitter']['result'] &&
                this.gathered['twitter']['result'][4] &&
                this.gathered['twitter']['result'][4]['graphic'] &&
                this.gathered['twitter']['result'][4]['graphic'][11] &&
                this.gathered['twitter']['result'][4]['graphic'][11]['twvsrt'] &&
                this.gathered['twitter']['result'][4]['graphic'][11]['twvsrt'].length > 0) {

                this.reportMessage = 'Twitter (Twitter) module...(Tweets vs ReTweets)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divTwitterTwvsrt');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                twint = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['twitter']['result'][4]['graphic'][11]['twvsrt'];

                for (const i in list) {
                    if (list[i]['title'] !== 'Users') {
                        elem = [list[i]['name'], list[i]['value']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Name', 'Value']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            if (!twint) {
                doc.setLineWidth(15);
                doc.setDrawColor('#00000');
                doc.line(20, 105, 190, 105);
                doc.line(20, 155, 190, 155);
                img.src = 'assets/images/ban.png';
                doc.addImage(img, 'png', 10, 105, 190, 50);
            }

            hl = hl + 10;
        }

        /////////////////////////////////////////////////////////////////
        // Instagram module report
        /////////////////////////////////////////////////////////////////
        if (this.gathered['instagram'] &&
            this.gathered['instagram']['result'] &&
            this.gathered['instagram']['result'].length > 3) {

            this.reportMessage = 'Instagram module...'

            let instagram = false;

            doc.addPage();
            doc.setFontSize(25);
            hl = 40;

            // Header title page
            img.src = 'assets/images/h1.jpg';
            doc.addImage(img, 'png', 100, 15, 100, 14);
            img.src = 'assets/images/iKy-Logo.png';
            doc.addImage(img, 'png', 185, 17, 10, 10);
            doc.setFontSize(12);
            doc.setTextColor('#05fcfc');
            doc.text('MODULE - Instagram', 105, 23);

            // Information table
            if (this.gathered['instagram'] &&
                this.gathered['instagram']['result'] &&
                this.gathered['instagram']['result'][4] &&
                this.gathered['instagram']['result'][4]['graphic'] &&
                this.gathered['instagram']['result'][4]['graphic'][0] &&
                this.gathered['instagram']['result'][4]['graphic'][0]['instagram'] &&
                this.gathered['instagram']['result'][4]['graphic'][0]['instagram'].length > 1) {

                this.reportMessage = 'Instagram module...(Social)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divInstagramSocial');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                instagram = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['instagram']['result'][4]['graphic'][0]['instagram'];

                for (const i in list) {
                    if (list[i]['title'] !== 'Instagram') {
                        elem = [list[i]['title'], list[i]['subtitle']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Name', 'Value']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // TODO: Images ??

            // Information table
            if (this.gathered['instagram'] &&
                this.gathered['instagram']['result'] &&
                this.gathered['instagram']['result'][4] &&
                this.gathered['instagram']['result'][4]['graphic'] &&
                this.gathered['instagram']['result'][4]['graphic'][3] &&
                this.gathered['instagram']['result'][4]['graphic'][3]['hashtags'] &&
                this.gathered['instagram']['result'][4]['graphic'][3]['hashtags'].length > 0) {

                this.reportMessage = 'Instagram module...(Hashtag)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divInstagramHashtag');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                instagram = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['instagram']['result'][4]['graphic'][3]['hashtags'];

                for (const i in list) {
                    if (list[i]['title'] !== 'Users') {
                        elem = [list[i]['label'], list[i]['value']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Hashtag', 'Ocurrences']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Instagram', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['instagram'] &&
                this.gathered['instagram']['result'] &&
                this.gathered['instagram']['result'][4] &&
                this.gathered['instagram']['result'][4]['graphic'] &&
                this.gathered['instagram']['result'][4]['graphic'][4] &&
                this.gathered['instagram']['result'][4]['graphic'][4]['mentions'] &&
                this.gathered['instagram']['result'][4]['graphic'][4]['mentions'].length > 0) {

                this.reportMessage = 'Instagram module...(Mentions)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divInstagramMention');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                instagram = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['instagram']['result'][4]['graphic'][4]['mentions'];

                for (const i in list) {
                    if (list[i]['title'] !== 'Users') {
                        elem = [list[i]['label'], list[i]['value']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Mention', 'Ocurrences']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Instagram', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['instagram'] &&
                this.gathered['instagram']['result'] &&
                this.gathered['instagram']['result'][4] &&
                this.gathered['instagram']['result'][4]['graphic'] &&
                this.gathered['instagram']['result'][4]['graphic'][5] &&
                this.gathered['instagram']['result'][4]['graphic'][5]['tagged'] &&
                this.gathered['instagram']['result'][4]['graphic'][5]['tagged'].length > 0) {

                this.reportMessage = 'Instagram module...(Tagged)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divInstagramTagged');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                instagram = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['instagram']['result'][4]['graphic'][5]['tagged'];

                for (const i in list) {
                    if (list[i]['title'] !== 'Users') {
                        elem = [list[i]['label'], list[i]['value']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Mention', 'Ocurrences']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,  
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Instagram', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['instagram'] &&
                this.gathered['instagram']['result'] &&
                this.gathered['instagram']['result'][4] &&
                this.gathered['instagram']['result'][4]['graphic'] &&
                this.gathered['instagram']['result'][4]['graphic'][6] &&
                this.gathered['instagram']['result'][4]['graphic'][6]['hour'] &&
                this.gathered['instagram']['result'][4]['graphic'][6]['hour'].length > 1) {

                this.reportMessage = 'Instagram module...(Hour)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divInstagramHour');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 60, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                instagram = true;

                hl = hl + 55;
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Instagram', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['instagram'] &&
                this.gathered['instagram']['result'] &&
                this.gathered['instagram']['result'][4] &&
                this.gathered['instagram']['result'][4]['graphic'] &&
                this.gathered['instagram']['result'][4]['graphic'][7] &&
                this.gathered['instagram']['result'][4]['graphic'][7]['week'] &&
                this.gathered['instagram']['result'][4]['graphic'][7]['week'].length > 1) {

                this.reportMessage = 'Instagram module...(Week)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divInstagramWeek');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 60, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                instagram = true;

                hl = hl + 55;
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Instagram', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['instagram'] &&
                this.gathered['instagram']['result'] &&
                this.gathered['instagram']['result'][4] &&
                this.gathered['instagram']['result'][4]['graphic'] &&
                this.gathered['instagram']['result'][4]['graphic'][1] &&
                this.gathered['instagram']['result'][4]['graphic'][1]['postslist'] &&
                this.gathered['instagram']['result'][4]['graphic'][1]['postslist'].length > 0) {

                this.reportMessage = 'Instagram module...(Post list)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divInstagramPosts');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                instagram = true;
                const bodyTable = [];
                let elem = [];
                const listlikes = this.gathered['instagram']['result'][4]['graphic'][1]['postslist'][0]['series'];
                const listcomm = this.gathered['instagram']['result'][4]['graphic'][1]['postslist'][1]['series'];

                for (const i in listlikes) {
                    elem = [listlikes[i]['name'], listlikes[i]['value'], listcomm[i]['value']];
                    bodyTable.push(elem);
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Post (Last)', 'Likes', 'Comments']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46'},
                         1: {fillColor: '#22262a'},
                         2: {fillColor: '#393f46'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Instagram', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['instagram'] &&
                this.gathered['instagram']['result'] &&
                this.gathered['instagram']['result'][4] &&
                this.gathered['instagram']['result'][4]['graphic'] &&
                this.gathered['instagram']['result'][4]['graphic'][8] &&
                this.gathered['instagram']['result'][4]['graphic'][8]['mediatype'] &&
                this.gathered['instagram']['result'][4]['graphic'][8]['mediatype'].length > 0) {

                this.reportMessage = 'Instagram module...(Mediatype)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divInstagramMediatype');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                instagram = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['instagram']['result'][4]['graphic'][8]['mediatype'];

                for (const i in list) {
                    if (list[i]['title'] !== 'Users') {
                        elem = [list[i]['name'], list[i]['value']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Name', 'Value']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46'},
                         1: {fillColor: '#22262a'},
                         2: {fillColor: '#393f46'},
                         3: {fillColor: '#22262a'},
                         4: {fillColor: '#393f46'},
                         5: {fillColor: '#22262a'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Instagram', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['instagram'] &&
                this.gathered['instagram']['result'] &&
                this.gathered['instagram']['result'][4] &&
                this.gathered['instagram']['result'][4]['graphic'] &&
                this.gathered['instagram']['result'][4]['graphic'][2] &&
                this.gathered['instagram']['result'][4]['graphic'][2]['postsloc'] &&
                this.gathered['instagram']['result'][4]['graphic'][2]['postsloc'].length > 0) {

                this.reportMessage = 'Instagram module...(Posts location)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divInstagramMap');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 25, hl, 160, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                instagram = true;
                const bodyTable = [];
                let elem = [];
                let list = this.gathered['instagram']['result'][4]['graphic'][2]['postsloc'];

                for (const i in list) {
                    elem = [list[i]['Name'], list[i]['Caption'], list[i]['Accessability'], list[i]['Latitude'], list[i]['Longitude'], list[i]['Time']];
                    bodyTable.push(elem);
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Name', 'Caption', 'Accessability', 'Lat', 'Long', 'Time']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46'},
                         1: {fillColor: '#22262a'},
                         2: {fillColor: '#393f46'},
                         3: {fillColor: '#22262a'},
                         4: {fillColor: '#393f46'},
                         5: {fillColor: '#22262a'},
                     },
                     margin: {top: 0, left: 15},
                     startY: hl + 60,
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            if (!instagram) {
                doc.setLineWidth(15);
                doc.setDrawColor('#00000');
                doc.line(20, 105, 190, 105);
                doc.line(20, 155, 190, 155);
                img.src = 'assets/images/ban.png';
                doc.addImage(img, 'png', 10, 105, 190, 50);
            }

            hl = hl + 10;
        }

        /////////////////////////////////////////////////////////////////
        // Linkedin module report
        /////////////////////////////////////////////////////////////////
        if (this.gathered['linkedin'] &&
            this.gathered['linkedin']['result'] &&
            this.gathered['linkedin']['result'].length > 3) {

            this.reportMessage = 'Linkedin module...'

            let linkedin = false;

            doc.addPage();
            doc.setFontSize(25);
            hl = 40;

            // Header title page
            img.src = 'assets/images/h1.jpg';
            doc.addImage(img, 'png', 100, 15, 100, 14);
            img.src = 'assets/images/iKy-Logo.png';
            doc.addImage(img, 'png', 185, 17, 10, 10);
            doc.setFontSize(12);
            doc.setTextColor('#05fcfc');
            doc.text('MODULE - Linkedin', 105, 23);

            // Information table
            if (this.gathered['linkedin'] &&
                this.gathered['linkedin']['result'] &&
                this.gathered['linkedin']['result'][4] &&
                this.gathered['linkedin']['result'][4]['graphic'] &&
                this.gathered['linkedin']['result'][4]['graphic'][0] &&
                this.gathered['linkedin']['result'][4]['graphic'][0]['social'] &&
                this.gathered['linkedin']['result'][4]['graphic'][0]['social'].length > 1) {

                this.reportMessage = 'Linkedin module...(Social)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divLinkedinGraphs');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                linkedin = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['linkedin']['result'][4]['graphic'][0]['social'];

                for (const i in list) {
                    if (list[i]['title'] !== 'Linkedin') {
                        elem = [list[i]['title'], list[i]['subtitle']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Name', 'Value']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Information table
            if (this.gathered['linkedin'] &&
                this.gathered['linkedin']['result'] &&
                this.gathered['linkedin']['result'][4] &&
                this.gathered['linkedin']['result'][4]['graphic'] &&
                this.gathered['linkedin']['result'][4]['graphic'][1] &&
                this.gathered['linkedin']['result'][4]['graphic'][1]['skills'] &&
                this.gathered['linkedin']['result'][4]['graphic'][1]['skills']['children'] &&
                this.gathered['linkedin']['result'][4]['graphic'][1]['skills']['children'].length > 0) {

                this.reportMessage = 'Linkedin module...(Skills)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divLinkedinBubble');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                linkedin = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['linkedin']['result'][4]['graphic'][1]['skills']['children'];

                for (const i in list) {
                    elem = [list[i]['name'], list[i]['count']];
                    bodyTable.push(elem);
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Area', 'Skill']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Linkedin', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['linkedin'] &&
                this.gathered['linkedin']['result'] &&
                this.gathered['linkedin']['result'][4] &&
                this.gathered['linkedin']['result'][4]['graphic'] &&
                this.gathered['linkedin']['result'][4]['graphic'][2] &&
                this.gathered['linkedin']['result'][4]['graphic'][2]['certificationView'] &&
                this.gathered['linkedin']['result'][4]['graphic'][2]['certificationView'].length > 0) {

                this.reportMessage = 'Linkedin module...(Certifications)'

                // Image

                linkedin = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['linkedin']['result'][4]['graphic'][2]['certificationView'];

                for (const i in list) {
                    elem = [list[i]['name'], list[i]['desc']];
                    bodyTable.push(elem);
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Certification', 'Description']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 5, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 5, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46'},
                         1: {fillColor: '#22262a'},
                     },
                     margin: {top: 0, left: 15},
                     startY: hl,
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                hl = finalY;
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Linkedin', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['linkedin'] &&
                this.gathered['linkedin']['result'] &&
                this.gathered['linkedin']['result'][4] &&
                this.gathered['linkedin']['result'][4]['graphic'] &&
                this.gathered['linkedin']['result'][4]['graphic'][3] &&
                this.gathered['linkedin']['result'][4]['graphic'][3]['positionGroupView'] &&
                this.gathered['linkedin']['result'][4]['graphic'][3]['positionGroupView'].length > 0) {

                this.reportMessage = 'Linkedin module...(Positions)'

                // Image

                linkedin = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['linkedin']['result'][4]['graphic'][3]['positionGroupView'];

                for (const i in list) {
                    elem = [list[i]['label']];
                    bodyTable.push(elem);
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Positions']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46'},
                         1: {fillColor: '#22262a'},
                     },
                     margin: {top: 0, left: 50, right: 50},
                     startY: hl,
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            if (!linkedin) {
                doc.setLineWidth(15);
                doc.setDrawColor('#00000');
                doc.line(20, 105, 190, 105);
                doc.line(20, 155, 190, 155);
                img.src = 'assets/images/ban.png';
                doc.addImage(img, 'png', 10, 105, 190, 50);
            }

            hl = hl + 10;
        }

        /////////////////////////////////////////////////////////////////
        // Github module report
        /////////////////////////////////////////////////////////////////
        if (this.gathered['github'] &&
            this.gathered['github']['result'] &&
            this.gathered['github']['result'].length > 3) {

            this.reportMessage = 'Instagram module...'

            let github = false;

            doc.addPage();
            doc.setFontSize(25);
            hl = 40;

            // Header title page
            img.src = 'assets/images/h1.jpg';
            doc.addImage(img, 'png', 100, 15, 100, 14);
            img.src = 'assets/images/iKy-Logo.png';
            doc.addImage(img, 'png', 185, 17, 10, 10);
            doc.setFontSize(12);
            doc.setTextColor('#05fcfc');
            doc.text('MODULE - Github', 105, 23);

            // Information table
            if (this.gathered['github'] &&
                this.gathered['github']['result'] &&
                this.gathered['github']['result'][4] &&
                this.gathered['github']['result'][4]['graphic'] &&
                this.gathered['github']['result'][4]['graphic'][0] &&
                this.gathered['github']['result'][4]['graphic'][0]['github'] &&
                this.gathered['github']['result'][4]['graphic'][0]['github'].length > 1) {

                this.reportMessage = 'Github module...(Social)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divGithubGraphs');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                github = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['github']['result'][4]['graphic'][0]['github'];

                for (const i in list) {
                    if (list[i]['title'] !== 'Github') {
                        elem = [list[i]['title'], list[i]['subtitle']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Name', 'Value']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Information table
            if (this.gathered['github'] &&
                this.gathered['github']['result'] &&
                this.gathered['github']['result'][4] &&
                this.gathered['github']['result'][4]['graphic'] &&
                this.gathered['github']['result'][4]['graphic'][1] &&
                this.gathered['github']['result'][4]['graphic'][1]['cal_actual'] &&
                this.gathered['github']['result'][4]['graphic'][1]['cal_actual'].length > 0) {

                this.reportMessage = 'Github module...(Calendar)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divGithubCalendar');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 25, hl, 160, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                github = true;
            }

            if (!github) {
                doc.setLineWidth(15);
                doc.setDrawColor('#00000');
                doc.line(20, 105, 190, 105);
                doc.line(20, 155, 190, 155);
                img.src = 'assets/images/ban.png';
                doc.addImage(img, 'png', 10, 105, 190, 50);
            }

            hl = hl + 10;
        }

        /////////////////////////////////////////////////////////////////
        // Keybase module report
        /////////////////////////////////////////////////////////////////
        if (this.gathered['keybase'] &&
            this.gathered['keybase']['result'] &&
            this.gathered['keybase']['result'].length > 3) {

            this.reportMessage = 'Keybase module...'

            let keybase = false;

            doc.addPage();
            doc.setFontSize(25);
            hl = 40;

            // Header title page
            img.src = 'assets/images/h1.jpg';
            doc.addImage(img, 'png', 100, 15, 100, 14);
            img.src = 'assets/images/iKy-Logo.png';
            doc.addImage(img, 'png', 185, 17, 10, 10);
            doc.setFontSize(12);
            doc.setTextColor('#05fcfc');
            doc.text('MODULE - Keybase', 105, 23);

            // Information table
            if (this.gathered['keybase'] &&
                this.gathered['keybase']['result'] &&
                this.gathered['keybase']['result'][4] &&
                this.gathered['keybase']['result'][4]['graphic'] &&
                this.gathered['keybase']['result'][4]['graphic'][0] &&
                this.gathered['keybase']['result'][4]['graphic'][0]['keysocial'] &&
                this.gathered['keybase']['result'][4]['graphic'][0]['keysocial'].length > 1) {

                this.reportMessage = 'Keybase module...(Social)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divKeybaseSocial');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                keybase = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['keybase']['result'][4]['graphic'][0]['keysocial'];

                for (const i in list) {
                    if (list[i]['title'] !== 'KeybaseSocial') {
                        elem = [list[i]['title'], list[i]['subtitle']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Name', 'Value']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Information table
            if (this.gathered['keybase'] &&
                this.gathered['keybase']['result'] &&
                this.gathered['keybase']['result'][4] &&
                this.gathered['keybase']['result'][4]['graphic'] &&
                this.gathered['keybase']['result'][4]['graphic'][1] &&
                this.gathered['keybase']['result'][4]['graphic'][1]['devices'] &&
                this.gathered['keybase']['result'][4]['graphic'][1]['devices'].length > 1) {

                this.reportMessage = 'Keybase module...(Devices)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divKeybaseDevices');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                keybase = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['keybase']['result'][4]['graphic'][1]['devices'];

                for (const i in list) {
                    if (list[i]['title'] !== 'Devices') {
                        elem = [list[i]['title'], list[i]['subtitle']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Name', 'Value']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            if (!keybase) {
                doc.setLineWidth(15);
                doc.setDrawColor('#00000');
                doc.line(20, 105, 190, 105);
                doc.line(20, 155, 190, 155);
                img.src = 'assets/images/ban.png';
                doc.addImage(img, 'png', 10, 105, 190, 50);
            }

            hl = hl + 10;
        }

        /////////////////////////////////////////////////////////////////
        // Spotify module report
        /////////////////////////////////////////////////////////////////
        if (this.gathered['spotify'] &&
            this.gathered['spotify']['result'] &&
            this.gathered['spotify']['result'].length > 3) {

            this.reportMessage = 'Spotify module...'

            let spotify = false;

            doc.addPage();
            doc.setFontSize(25);
            hl = 40;

            // Header title page
            img.src = 'assets/images/h1.jpg';
            doc.addImage(img, 'png', 100, 15, 100, 14);
            img.src = 'assets/images/iKy-Logo.png';
            doc.addImage(img, 'png', 185, 17, 10, 10);
            doc.setFontSize(12);
            doc.setTextColor('#05fcfc');
            doc.text('MODULE - Spotify', 105, 23);

            // Information table
            if (this.gathered['spotify'] &&
                this.gathered['spotify']['result'] &&
                this.gathered['spotify']['result'][4] &&
                this.gathered['spotify']['result'][4]['graphic'] &&
                this.gathered['spotify']['result'][4]['graphic'][0] &&
                this.gathered['spotify']['result'][4]['graphic'][0]['social'] &&
                this.gathered['spotify']['result'][4]['graphic'][0]['social'].length > 1) {

                this.reportMessage = 'Spotify module...(Social)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divSpotifySocial');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                spotify = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['spotify']['result'][4]['graphic'][0]['social'];

                for (const i in list) {
                    if (list[i]['title'] !== 'Spotify') {
                        elem = [list[i]['title'], list[i]['subtitle']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Name', 'Value']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // TODO : Playlist

            // Information table
            if (this.gathered['spotify'] &&
                this.gathered['spotify']['result'] &&
                this.gathered['spotify']['result'][4] &&
                this.gathered['spotify']['result'][4]['graphic'] &&
                this.gathered['spotify']['result'][4]['graphic'][2] &&
                this.gathered['spotify']['result'][4]['graphic'][2]['autors'] &&
                this.gathered['spotify']['result'][4]['graphic'][2]['autors'].length > 1) {

                this.reportMessage = 'Spotify module...(Authors)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divSpotifyAutors');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                spotify = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['spotify']['result'][4]['graphic'][2]['autors'];
                list.sort((a, b)=> (a.value < b.value ? 1 : -1))

                let a = 0;
                for (const i in list) {
                    if (a === 16) {
                        break;
                    }
                    elem = [list[i]['label'], list[i]['value']];
                    bodyTable.push(elem);
                    a = a + 1;
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Author', 'Ocurrences']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     // pageBreak: 'always',
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Spotify', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['spotify'] &&
                this.gathered['spotify']['result'] &&
                this.gathered['spotify']['result'][4] &&
                this.gathered['spotify']['result'][4]['graphic'] &&
                this.gathered['spotify']['result'][4]['graphic'][3] &&
                this.gathered['spotify']['result'][4]['graphic'][3]['words'] &&
                this.gathered['spotify']['result'][4]['graphic'][3]['words'].length > 1) {

                this.reportMessage = 'Spotify module...(Words)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divSpotifyWords');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                spotify = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['spotify']['result'][4]['graphic'][3]['words'];
                list.sort((a, b)=> (a.value < b.value ? 1 : -1))

                let a = 0;
                for (const i in list) {
                    if (a === 16) {
                        break;
                    }
                    elem = [list[i]['label'], list[i]['value']];
                    bodyTable.push(elem);
                    a = a + 1;
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Word', 'Ocurrences']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     // pageBreak: 'always',
                     startY: hl,
                     didDrawPage: function (data) {
                          data.settings.margin.top = 30; }
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Spotify', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['spotify'] &&
                this.gathered['spotify']['result'] &&
                this.gathered['spotify']['result'][4] &&
                this.gathered['spotify']['result'][4]['graphic'] &&
                this.gathered['spotify']['result'][4]['graphic'][4] &&
                this.gathered['spotify']['result'][4]['graphic'][4]['lang'] &&
                this.gathered['spotify']['result'][4]['graphic'][4]['lang'].length > 1) {

                this.reportMessage = 'Spotify module...(Language)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divSpotifyLang');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                spotify = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['spotify']['result'][4]['graphic'][4]['lang'];
                list.sort((a, b)=> (a.value < b.value ? 1 : -1))

                let a = 0;
                for (const i in list) {
                    if (a === 7) {
                        break;
                    }
                    elem = [list[i]['name'], list[i]['value']];
                    bodyTable.push(elem);
                    a = a + 1;
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Name', 'Value']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }
            if (!spotify) {
                doc.setLineWidth(15);
                doc.setDrawColor('#00000');
                doc.line(20, 105, 190, 105);
                doc.line(20, 155, 190, 155);
                img.src = 'assets/images/ban.png';
                doc.addImage(img, 'png', 10, 105, 190, 50);
            }

            hl = hl + 10;
        }

        /////////////////////////////////////////////////////////////////
        // Reddit module report
        /////////////////////////////////////////////////////////////////
        if (this.gathered['reddit'] &&
            this.gathered['reddit']['result'] &&
            this.gathered['reddit']['result'].length > 3) {

            this.reportMessage = 'Reddit module...'

            let reddit = false;

            doc.addPage();
            doc.setFontSize(25);
            hl = 40;

            // Header title page
            img.src = 'assets/images/h1.jpg';
            doc.addImage(img, 'png', 100, 15, 100, 14);
            img.src = 'assets/images/iKy-Logo.png';
            doc.addImage(img, 'png', 185, 17, 10, 10);
            doc.setFontSize(12);
            doc.setTextColor('#05fcfc');
            doc.text('MODULE - Reddit', 105, 23);

            // Information table
            if (this.gathered['reddit'] &&
                this.gathered['reddit']['result'] &&
                this.gathered['reddit']['result'][4] &&
                this.gathered['reddit']['result'][4]['graphic'] &&
                this.gathered['reddit']['result'][4]['graphic'][0] &&
                this.gathered['reddit']['result'][4]['graphic'][0]['social'] &&
                this.gathered['reddit']['result'][4]['graphic'][0]['social'].length > 1) {

                this.reportMessage = 'Reddit module...(Social)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divRedditSocial');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                reddit = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['reddit']['result'][4]['graphic'][0]['social'];

                for (const i in list) {
                    if (list[i]['title'] !== 'Reddit') {
                        elem = [list[i]['title'], list[i]['subtitle']];
                        bodyTable.push(elem);
                    }
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Name', 'Value']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }

            hl = hl + 20;

            // Information table
            if (this.gathered['reddit'] &&
                this.gathered['reddit']['result'] &&
                this.gathered['reddit']['result'][4] &&
                this.gathered['reddit']['result'][4]['graphic'] &&
                this.gathered['reddit']['result'][4]['graphic'][1] &&
                this.gathered['reddit']['result'][4]['graphic'][1]['hour'] &&
                this.gathered['reddit']['result'][4]['graphic'][1]['hour'].length > 0) {

                this.reportMessage = 'Reddit module...(Hour)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divRedditHour');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 60, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                reddit = true;

                hl = hl + 55;
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Reddit', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['reddit'] &&
                this.gathered['reddit']['result'] &&
                this.gathered['reddit']['result'][4] &&
                this.gathered['reddit']['result'][4]['graphic'] &&
                this.gathered['reddit']['result'][4]['graphic'][2] &&
                this.gathered['reddit']['result'][4]['graphic'][2]['week'] &&
                this.gathered['reddit']['result'][4]['graphic'][2]['week'].length > 0) {

                this.reportMessage = 'Reddit module...(Week)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divRedditWeek');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 60, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });
                instagram = true;

                hl = hl + 55;
            }

            hl = hl + 20;

            // Validate pageHeight
            if ( hl + 60 > pageHeight) {
                doc.addPage();
                doc.setFontSize(25);

                // Header title page
                img.src = 'assets/images/h1.jpg';
                doc.addImage(img, 'png', 100, 15, 100, 14);
                img.src = 'assets/images/iKy-Logo.png';
                doc.addImage(img, 'png', 185, 17, 10, 10);
                doc.setFontSize(12);
                doc.setTextColor('#05fcfc');
                doc.text('MODULE - Reddit', 105, 23);

                hl = 40;
            }

            // Information table
            if (this.gathered['reddit'] &&
                this.gathered['reddit']['result'] &&
                this.gathered['reddit']['result'][4] &&
                this.gathered['reddit']['result'][4]['graphic'] &&
                this.gathered['reddit']['result'][4]['graphic'][3] &&
                this.gathered['reddit']['result'][4]['graphic'][3]['topics'] &&
                this.gathered['reddit']['result'][4]['graphic'][3]['topics']['children'] &&
                this.gathered['reddit']['result'][4]['graphic'][3]['topics']['children'].length > 0) {

                this.reportMessage = 'Reddit module...(Topics)'

                // Image
                svg = this.nbCardContainer.nativeElement.querySelector('#divRedditBubble');

                await htmlToImage.toPng(svg)
                  .then(function (dataUrl) {
                    imgiKy.src = dataUrl;
                    doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
                  })
                  .catch(function (error) {
                    console.error('oops, something went wrong!', error);
                  });

                reddit = true;
                const bodyTable = [];
                let elem = [];
                const list = this.gathered['reddit']['result'][4]['graphic'][3]['topics']['children'];
                list.sort((a, b)=> (a.value < b.value ? 1 : -1))

                let a = 0;
                for (const i in list) {
                    if (a === 16) {
                        break;
                    }
                    elem = [list[i]['name'], list[i]['value']];
                    bodyTable.push(elem);
                    a = a + 1;
                }

                doc.setFontSize(10);
                autoTable(doc, {
                     head: [['Topic', 'Value']],
                     body: bodyTable,
                     headStyles: {fillColor: '#50fcfc',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  halign: 'center',
                                  textColor: '#000000',
                                  lineColor: '#1A1A1A'},
                     bodyStyles: {fillColor: '#1A1A1A',
                                  cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
                                  lineWidth: 1,
                                  fontSize: 8,
                                  textColor: '#50fcfc',
                                  lineColor: '#1A1A1A'},
                     columnStyles: {
                         0: {fillColor: '#393f46', cellWidth: 50},
                         1: {fillColor: '#22262a', halign: 'center'},
                     },
                     margin: {top: 0, left: 100},
                     startY: hl,
                });

                const finalY = (doc as any).lastAutoTable.finalY;
                if (hl + 55 < finalY) {
                    hl = finalY
                } else {
                    hl = hl + 55
                }
            }
            if (!reddit) {
                doc.setLineWidth(15);
                doc.setDrawColor('#00000');
                doc.line(20, 105, 190, 105);
                doc.line(20, 155, 190, 155);
                img.src = 'assets/images/ban.png';
                doc.addImage(img, 'png', 10, 105, 190, 50);
            }

            hl = hl + 10;
        }

        /////////////////////////////////////////////////////////////////
        // Twitch module report
        /////////////////////////////////////////////////////////////////
        // if (this.gathered['twitch'] &&
        //     this.gathered['twitch']['result'] &&
        //     this.gathered['twitch']['result'].length > 3) {

        //     this.reportMessage = 'Twitch module...'

        //     let twitch = false;

        //     doc.addPage();
        //     doc.setFontSize(25);
        //     hl = 40;

        //     // Header title page
        //     img.src = 'assets/images/h1.jpg';
        //     doc.addImage(img, 'png', 100, 15, 100, 14);
        //     img.src = 'assets/images/iKy-Logo.png';
        //     doc.addImage(img, 'png', 185, 17, 10, 10);
        //     doc.setFontSize(12);
        //     doc.setTextColor('#05fcfc');
        //     doc.text('MODULE - Twitch', 105, 23);

        //     // Information table
        //     if (this.gathered['twitch'] &&
        //         this.gathered['twitch']['result'] &&
        //         this.gathered['twitch']['result'][4] &&
        //         this.gathered['twitch']['result'][4]['graphic'] &&
        //         this.gathered['twitch']['result'][4]['graphic'][0] &&
        //         this.gathered['twitch']['result'][4]['graphic'][0]['social'] &&
        //         this.gathered['twitch']['result'][4]['graphic'][0]['social'].length > 1) {

        //         this.reportMessage = 'Twitch module...(Social)'

        //         // Image
        //         svg = this.nbCardContainer.nativeElement.querySelector('#divTwitchSocial');

        //         await htmlToImage.toPng(svg)
        //           .then(function (dataUrl) {
        //             imgiKy.src = dataUrl;
        //             doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
        //           })
        //           .catch(function (error) {
        //             console.error('oops, something went wrong!', error);
        //           });

        //         twitch = true;
        //         const bodyTable = [];
        //         let elem = [];
        //         const list = this.gathered['twitch']['result'][4]['graphic'][0]['social'];

        //         for (const i in list) {
        //             if (list[i]['title'] !== 'Twitch') {
        //                 elem = [list[i]['title'], list[i]['subtitle']];
        //                 bodyTable.push(elem);
        //             }
        //         }

        //         doc.setFontSize(10);
        //         autoTable(doc, {
        //              head: [['Name', 'Value']],
        //              body: bodyTable,
        //              headStyles: {fillColor: '#50fcfc',
        //                           cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
        //                           lineWidth: 1,
        //                           halign: 'center',
        //                           textColor: '#000000',
        //                           lineColor: '#1A1A1A'},
        //              bodyStyles: {fillColor: '#1A1A1A',
        //                           cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
        //                           lineWidth: 1,
        //                           fontSize: 8,
        //                           textColor: '#50fcfc',
        //                           lineColor: '#1A1A1A'},
        //              columnStyles: {
        //                  0: {fillColor: '#393f46', cellWidth: 50},
        //                  1: {fillColor: '#22262a', halign: 'center'},
        //              },
        //              margin: {top: 0, left: 100},
        //              startY: hl,
        //         });

        //         const finalY = (doc as any).lastAutoTable.finalY;
        //         if (hl + 55 < finalY) {
        //             hl = finalY
        //         } else {
        //             hl = hl + 55
        //         }
        //     }

        //     hl = hl + 20;

        //     // Information table
        //     if (this.gathered['twitch'] &&
        //         this.gathered['twitch']['result'] &&
        //         this.gathered['twitch']['result'][4] &&
        //         this.gathered['twitch']['result'][4]['graphic'] &&
        //         this.gathered['twitch']['result'][4]['graphic'][5] &&
        //         this.gathered['twitch']['result'][4]['graphic'][5]['hour'] &&
        //         this.gathered['twitch']['result'][4]['graphic'][5]['hour'].length > 0) {

        //         this.reportMessage = 'Twitch module...(Hour)'

        //         // Image
        //         svg = this.nbCardContainer.nativeElement.querySelector('#divTwitchHour');

        //         await htmlToImage.toPng(svg)
        //           .then(function (dataUrl) {
        //             imgiKy.src = dataUrl;
        //             doc.addImage(imgiKy, 'png', 60, hl, 75, 55);
        //           })
        //           .catch(function (error) {
        //             console.error('oops, something went wrong!', error);
        //           });
        //         twitch = true;

        //         hl = hl + 55;
        //     }

        //     hl = hl + 20;

        //     // Validate pageHeight
        //     if ( hl + 60 > pageHeight) {
        //         doc.addPage();
        //         doc.setFontSize(25);

        //         // Header title page
        //         img.src = 'assets/images/h1.jpg';
        //         doc.addImage(img, 'png', 100, 15, 100, 14);
        //         img.src = 'assets/images/iKy-Logo.png';
        //         doc.addImage(img, 'png', 185, 17, 10, 10);
        //         doc.setFontSize(12);
        //         doc.setTextColor('#05fcfc');
        //         doc.text('MODULE - Twitch', 105, 23);

        //         hl = 40;
        //     }

        //     // Information table
        //     if (this.gathered['reddit'] &&
        //         this.gathered['reddit']['result'] &&
        //         this.gathered['reddit']['result'][4] &&
        //         this.gathered['reddit']['result'][4]['graphic'] &&
        //         this.gathered['reddit']['result'][4]['graphic'][2] &&
        //         this.gathered['reddit']['result'][4]['graphic'][2]['week'] &&
        //         this.gathered['reddit']['result'][4]['graphic'][2]['week'].length > 0) {

        //         this.reportMessage = 'Reddit module...(Week)'

        //         // Image
        //         svg = this.nbCardContainer.nativeElement.querySelector('#divRedditWeek');

        //         await htmlToImage.toPng(svg)
        //           .then(function (dataUrl) {
        //             imgiKy.src = dataUrl;
        //             doc.addImage(imgiKy, 'png', 60, hl, 75, 55);
        //           })
        //           .catch(function (error) {
        //             console.error('oops, something went wrong!', error);
        //           });
        //         instagram = true;

        //         hl = hl + 55;
        //     }

        //     hl = hl + 20;

        //     // Validate pageHeight
        //     if ( hl + 60 > pageHeight) {
        //         doc.addPage();
        //         doc.setFontSize(25);

        //         // Header title page
        //         img.src = 'assets/images/h1.jpg';
        //         doc.addImage(img, 'png', 100, 15, 100, 14);
        //         img.src = 'assets/images/iKy-Logo.png';
        //         doc.addImage(img, 'png', 185, 17, 10, 10);
        //         doc.setFontSize(12);
        //         doc.setTextColor('#05fcfc');
        //         doc.text('MODULE - Reddit', 105, 23);

        //         hl = 40;
        //     }

        //     // Information table
        //     if (this.gathered['reddit'] &&
        //         this.gathered['reddit']['result'] &&
        //         this.gathered['reddit']['result'][4] &&
        //         this.gathered['reddit']['result'][4]['graphic'] &&
        //         this.gathered['reddit']['result'][4]['graphic'][3] &&
        //         this.gathered['reddit']['result'][4]['graphic'][3]['topics'] &&
        //         this.gathered['reddit']['result'][4]['graphic'][3]['topics']['children'] &&
        //         this.gathered['reddit']['result'][4]['graphic'][3]['topics']['children'].length > 0) {

        //         this.reportMessage = 'Reddit module...(Topics)'

        //         // Image
        //         svg = this.nbCardContainer.nativeElement.querySelector('#divRedditBubble');

        //         await htmlToImage.toPng(svg)
        //           .then(function (dataUrl) {
        //             imgiKy.src = dataUrl;
        //             doc.addImage(imgiKy, 'png', 10, hl, 75, 55);
        //           })
        //           .catch(function (error) {
        //             console.error('oops, something went wrong!', error);
        //           });

        //         reddit = true;
        //         const bodyTable = [];
        //         let elem = [];
        //         const list = this.gathered['reddit']['result'][4]['graphic'][3]['topics']['children'];
        //         list.sort((a, b)=> (a.value < b.value ? 1 : -1))

        //         let a = 0;
        //         for (const i in list) {
        //             if (a === 16) {
        //                 break;
        //             }
        //             elem = [list[i]['name'], list[i]['value']];
        //             bodyTable.push(elem);
        //             a = a + 1;
        //         }

        //         doc.setFontSize(10);
        //         autoTable(doc, {
        //              head: [['Topic', 'Value']],
        //              body: bodyTable,
        //              headStyles: {fillColor: '#50fcfc',
        //                           cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
        //                           lineWidth: 1,
        //                           halign: 'center',
        //                           textColor: '#000000',
        //                           lineColor: '#1A1A1A'},
        //              bodyStyles: {fillColor: '#1A1A1A',
        //                           cellPadding: {top: 2, right: 2, bottom: 2, left: 5},
        //                           lineWidth: 1,
        //                           fontSize: 8,
        //                           textColor: '#50fcfc',
        //                           lineColor: '#1A1A1A'},
        //              columnStyles: {
        //                  0: {fillColor: '#393f46', cellWidth: 50},
        //                  1: {fillColor: '#22262a', halign: 'center'},
        //              },
        //              margin: {top: 0, left: 100},
        //              startY: hl,
        //         });

        //         const finalY = (doc as any).lastAutoTable.finalY;
        //         if (hl + 55 < finalY) {
        //             hl = finalY
        //         } else {
        //             hl = hl + 55
        //         }
        //     }
        //     if (!reddit) {
        //         doc.setLineWidth(15);
        //         doc.setDrawColor('#00000');
        //         doc.line(20, 105, 190, 105);
        //         doc.line(20, 155, 190, 155);
        //         img.src = 'assets/images/ban.png';
        //         doc.addImage(img, 'png', 10, 105, 190, 50);
        //     }

        //     hl = hl + 10;
        // }
        /////////////////////////////////////////////////////////////////
        // END
        /////////////////////////////////////////////////////////////////
        this.reportEnd = true;
        this.reportMessage = 'Report DONE';

        this.report = doc;
        // doc.save('Report_iKy_' + Date.now() + '.pdf');
        this.processing = false;
    }

    //    async generateAllPdf() {
    //        this.processing = true;
    //        var infoText: string;
    //        let moduleHeight: number;
    //        this.profile = [];
    //        this.timeline = [];
    //        this.name = [];
    //        this.location = [];
    //        this.gender = [];
    //        this.organization = [];
    //        this.social = [];
    //        this.photo = [];
    //
    //        const doc2 = new jsPDF()
    //        doc2.autoTable({ html: '#my-table' })
    //        doc2.save('table.pdf')
    //
    //        const doc = new jsPDF('p', 'mm', 'a4');
    //        var pageHeight = doc.internal.pageSize.height;
    //        
    //        doc.setFontSize(25);
    //        // doc.setFontStyle('bold');
    //        var img = new Image()
    //        // img.src = 'assets/images/iKy-Logo.png'
    //        img.src = 'favicon-32x32.png'
    //        doc.addImage(img, 'png', 65, 60, 80, 80)
    //        doc.text('Report', 105, 160, {align: 'center'});
    //        doc.text('Report', 105, 160);
    //        doc.addPage();
    //        var hl = 20;
    //        
    //        doc.setDrawColor(32, 61, 79);
    //        doc.setFillColor(32, 61, 79);
    //        doc.rect(10, hl, 190, 7, 'F');
    //        doc.rect(10, hl, 190, 13); 
    //        
    //        doc.setFontSize(11);
    //        doc.setTextColor(255, 255, 255);
    //        doc.text('Analyzed email', 105, hl + 5, {align: 'center'});
    //        doc.setFontSize(11);
    //        doc.setTextColor(0, 0, 0);
    //        doc.text(this.gathered['email'], 105, hl + 11, {align: 'center'});
    //        hl = hl + 20;
    //        
    //        doc.setFontSize(11);
    //        doc.setDrawColor(32, 61, 79);
    //        doc.setFillColor(32, 61, 79);
    //        doc.rect(10, hl, 190, 7, 'F');
    //        doc.setTextColor(255, 255, 255);
    //        doc.text('Information gathered', 105, hl + 5, {align: 'center'});
    //        hl = hl + 11;
    //        // 
    //        //         // EmailrepIO module report
    //        //         if (this.gathered['emailrep'] && this.gathered['emailrep']['result'] && 
    //        //                 this.gathered['linkedin']['result'].length > 3) {
    //        //             moduleHeight = 80;
    //        // 
    //        //             // Validate pageHeight
    //        //             if ( hl + moduleHeight > pageHeight) {
    //        //                 doc.addPage();
    //        //                 hl = 20;
    //        //             }
    //        // 
    //        //             // EmailRep
    //        //             doc.setFontSize(11);
    //        //             doc.setDrawColor(44, 93, 126);
    //        //             doc.setFillColor(44, 93, 126);
    //        //             doc.rect(10, hl, 190, 7, 'F');
    //        //             doc.setTextColor(255, 255, 255);
    //        //             doc.text('Module emailrep', 105, hl + 5, null, null, 'center');
    //        //             hl = hl + 10;
    //        // 
    //        //             var svg = this.nbCardContainer.nativeElement.querySelector('#divEmailrepInfo');
    //        //             var svg2 = svg.children[0].children[0].children[1].children[0].children[0].children[0];
    //        //             await html2canvas(svg2, { 
    //        //                 // scale: 1,
    //        //                 useCORS: true, 
    //        //                 // foreignObjectRendering: true,  // Render with the background but only if the div is in the screen
    //        //                 // logging: false,
    //        //                 backgroundColor: '#333333',
    //        //                 allowTaint: true,
    //        //                 // removeContainer: false
    //        //                 })
    //        //                 .then(function (canvas) { 
    //        //                     doc.addImage(canvas.toDataURL('image/png'), 'JPEG', 10, hl, 75, 55);
    //        //                 });
    //        // 
    //        //             doc.setFontSize(11);
    //        //             doc.setFont('helvetica', 'normal');
    //        //             doc.setTextColor(79, 79, 79);
    //        //             infoText = 'The information of the chart is shown in the following table.';
    //        //             var splitText = doc.splitTextToSize(infoText, 110);
    //        //             var y = 6;
    //        //             for (var i=0; i<splitText.length; i++){
    //        //                 doc.text(90, hl + y, splitText[i]);
    //        //                 y = y + 4;
    //        //             }
    //        // 
    //        //             // Information table
    //        //             if (this.gathered['emailrep']['result'][4]['graphic'][0]['details']) {
    //        //                 let headTable = [];
    //        //                 let bodyTable = [];
    //        //                 let elem = [];
    //        //                 let i: any;
    //        //                 let list = this.gathered['emailrep']['result'][4]['graphic'][0]['details'];
    //        //                 
    //        //                 for (let i in list) {
    //        //                     if (list[i]['title'] != 'EmailRep') {
    //        //                         elem = [list[i]['title'], list[i]['subtitle']];
    //        //                         bodyTable.push(elem);
    //        //                     }
    //        //                 }
    //        // 
    //        //                 doc.autoTable({
    //        //                     startY: hl + 11,
    //        //                     margin: {left: 90},
    //        //                     showHead: false,
    //        //                     styles: { overflow: 'hidden' },
    //        //                     bodyStyles: {
    //        //                         fillColor: [52, 73, 94],
    //        //                         textColor: 240
    //        //                     },
    //        //                     alternateRowStyles: {
    //        //                         fillColor: [74, 96, 117]
    //        //                     },
    //        //                     head: [
    //        //                         ['Name', 'Value'],
    //        //                     ],
    //        //                     body: bodyTable,
    //        //                 });
    //        // 
    //        //                 let finalY = doc.previousAutoTable.finalY;
    //        //                 doc.autoTable({
    //        //                     startY: finalY,
    //        //                     // html: '.table',
    //        //                     useCss: true,
    //        //                 });
    //        //         
    //        //                 hl = finalY
    //        //             }
    //        // 
    //        //             hl = hl + 10;
    //        // 
    //        //             var svg = this.nbCardContainer.nativeElement.querySelector('#divEmailrepSocial');
    //        //             var svg2 = svg.children[0].children[0].children[1].children[0].children[0].children[0];
    //        //             await html2canvas(svg2, { 
    //        //                 // scale: 1,
    //        //                 useCORS: true, 
    //        //                 // foreignObjectRendering: true,  // Render with the background but only if the div is in the screen
    //        //                 // logging: false,
    //        //                 backgroundColor: '#333333',
    //        //                 allowTaint: true,
    //        //                 // removeContainer: false
    //        //                 })
    //        //                 .then(function (canvas) { 
    //        //                     doc.addImage(canvas.toDataURL('image/png'), 'JPEG', 10, hl, 75, 55);
    //        //                 });
    //        // 
    //        //             doc.setFontSize(11);
    //        //             doc.setFont('helvetica', 'normal');
    //        //             doc.setTextColor(79, 79, 79);
    //        //             infoText = 'The information of the chart is shown in the following table.';
    //        //             var splitText = doc.splitTextToSize(infoText, 110);
    //        //             var y = 6;
    //        //             for (var i=0; i<splitText.length; i++){
    //        //                 doc.text(90, hl + y, splitText[i]);
    //        //                 y = y + 4;
    //        //             }
    //        // 
    //        //             // Information table
    //        //             if (this.gathered['emailrep']['result'][4]['graphic'][1]['social']) {
    //        //                 let headTable = [];
    //        //                 let bodyTable = [];
    //        //                 let elem = [];
    //        //                 let i: any;
    //        //                 let list = this.gathered['emailrep']['result'][4]['graphic'][1]['social'];
    //        //                 
    //        //                 for (let i in list) {
    //        //                     if (list[i]['title'] != 'EmailRep') {
    //        //                         elem = [list[i]['title'], list[i]['subtitle']];
    //        //                         bodyTable.push(elem);
    //        //                     }
    //        //                 }
    //        // 
    //        //                 doc.autoTable({
    //        //                     startY: hl + 11,
    //        //                     margin: {left: 90},
    //        //                     showHead: false,
    //        //                     styles: { overflow: 'hidden' },
    //        //                     bodyStyles: {
    //        //                         fillColor: [52, 73, 94],
    //        //                         textColor: 240
    //        //                     },
    //        //                     alternateRowStyles: {
    //        //                         fillColor: [74, 96, 117]
    //        //                     },
    //        //                     head: [
    //        //                         ['Name', 'Value'],
    //        //                     ],
    //        //                     body: bodyTable,
    //        //                 });
    //        // 
    //        //                 let finalY = doc.previousAutoTable.finalY;
    //        //                 doc.autoTable({
    //        //                     startY: finalY,
    //        //                     // html: '.table',
    //        //                     useCss: true,
    //        //                 });
    //        //         
    //        //                 hl = finalY
    //        //             }
    //        // 
    //        //             hl = hl + 10;
    //        //         }
    //        // 
    //        // 
    //        // Fullcontact module report
    //        if (this.gathered['fullcontact'] && this.gathered['fullcontact']['result'] && 
    //              this.gathered['fullcontact']['result'].length > 3) {
    //            moduleHeight = 80;
    //        
    //            // Validate pageHeight
    //            if ( hl + moduleHeight > pageHeight) {
    //                doc.addPage();
    //                hl = 20;
    //            }
    //        
    //            doc.setFontSize(11);
    //            doc.setDrawColor(44, 93, 126);
    //            doc.setFillColor(44, 93, 126);
    //            doc.rect(10, hl, 190, 7, 'F');
    //            doc.setTextColor(256, 255, 255);
    //            doc.text('Module fullcontact', 105, hl + 5, {align: 'center'});
    //            hl = hl + 10;
    //        
    //            var svg = this.nbCardContainer.nativeElement.querySelector('#divFullcontactGraphs');
    //            var svg2 = svg.children[0].children[0].children[1].children[0].children[0].children[0];
    //            // await html2canvas(svg.children[0], { 
    //            await html2canvas(svg2, { 
    //                // scale: 1,
    //                useCORS: true, 
    //                // foreignObjectRendering: true,  // Render with the background but only if the div is in the screen
    //                // logging: false,
    //                backgroundColor: '#333333',
    //                allowTaint: true,
    //                // removeContainer: false
    //                })
    //                .then(function (canvas) { 
    //                    doc.addImage(canvas.toDataURL('image/png'), 'JPEG', 10, hl, 75, 55);
    //                });
    //        
    //            // var svg = this.nbCardContainer.nativeElement.querySelector('#divFullcontactGraphs');
    //            // await html2canvas(svg.children[0], { 
    //            //     scale: 1,
    //            //     useCORS: true, 
    //            //     // foreignObjectRendering: true,  // Render with the background but only if the div is in the screen
    //            //     logging: true,
    //            //     backgroundColor: '#51A5D7',
    //            //     allowTaint: true,
    //            //     removeContainer: true
    //            //     })
    //            //     .then(function (canvas) { 
    //            //         doc.addImage(canvas.toDataURL('image/png'), 'JPEG', 10, hl, 75, 65);
    //            //     });
    //        
    //            doc.setFontSize(11);
    //            doc.setFont('helvetica', 'normal');
    //            doc.setTextColor(79, 79, 79);
    //            infoText = 'The information collected by the fullcontact module represented in the graph on the left shows the RRSS related to the e-mail analyzed.\n\nThe graph shows nodes, which have the name of the RRSS as upper title and the username in the lower part.\n\nThe information shown in the graph is shown in the table below.'
    //            var splitText = doc.splitTextToSize(infoText, 110);
    //            var y = 6;
    //            for (var i=0; i<splitText.length; i++){
    //                doc.text(splitText[i], 90, hl + y);
    //                y = y + 4;
    //            }
    //            hl = hl + 70;
    //        
    //            // Information table  TODO: Repair
    //            if (this.gathered['fullcontact']['result'][5]['profile'][5]['social']) {
    //                let headTable = [];
    //                let bodyTable = [];
    //                let elem = [];
    //                let i: any;
    //                let list = this.gathered['fullcontact']['result'][5]['profile'][5]['social'];
    //                
    //                for (let i in list) {
    //                    elem = [list[i]['name'], list[i]['username'], list[i]['url']];
    //                    bodyTable.push(elem);
    //                }
    //        
    //                doc.autoTable({
    //                    startY: hl,
    //                    head: [
    //                        ['RRSS', 'Username', 'Link'],
    //                    ],
    //                    body: bodyTable,
    //                });
    //            
    //                let finalY = doc.previousAutoTable.finalY;
    //                doc.autoTable({
    //                    startY: finalY,
    //                    // html: '.table',
    //                    useCss: true,
    //                });
    //        
    //                hl = finalY
    //            }
    //        }
    //        
    //        hl = hl + 10; // Space between modules
    //        // 
    //        // 
    //        //         // Twitter module report
    //        //         if (this.gathered['twitter'] && this.gathered['twitter']['result'] &&
    //        //               this.gathered['twitter']['result'].length > 3) {
    //        // 
    //        //             // Mentions user
    //        //             moduleHeight = 80;
    //        // 
    //        //             // Validate pageHeight
    //        //             if ( hl + moduleHeight > pageHeight) {
    //        //                 doc.addPage();
    //        //                 hl = 20;
    //        //             }
    //        // 
    //        //             doc.setFontSize(11);
    //        //             doc.setDrawColor(44, 93, 126);
    //        //             doc.setFillColor(44, 93, 126);
    //        //             doc.rect(10, hl, 190, 7, 'F');
    //        //             doc.setTextColor(255, 255, 255);
    //        //             doc.text('Module twitter', 105, hl + 5, null, null, 'center');
    //        //             hl = hl + 10;
    //        // 
    //        //             var svg = this.nbCardContainer.nativeElement.querySelector('#divTwitterList');
    //        //             var svg2 = svg.children[0].children[0].children[1].children[0].children[0].children[0];
    //        //             // await html2canvas(svg.children[0], { 
    //        //             await html2canvas(svg2, { 
    //        //                 // scale: 1,
    //        //                 useCORS: true, 
    //        //                 // foreignObjectRendering: true,  // Render with the background but only if the div is in the screen
    //        //                 // logging: false,
    //        //                 backgroundColor: '#888888',
    //        //                 allowTaint: true,
    //        //                 // removeContainer: false
    //        //                 })
    //        //                 .then(function (canvas) { 
    //        //                     doc.addImage(canvas.toDataURL('image/png'), 'JPEG', 10, hl, 75, 55);
    //        //                 });
    //        // 
    //        //             // Information table
    //        //             if (this.gathered['twitter']['result'][4]['graphic'][5]['tweetslist']) {
    //        //                 let headTable = [];
    //        //                 let bodyTable = [];
    //        //                 let elem = [];
    //        //                 let i: any;
    //        //                 let list = this.gathered['twitter']['result'][4]['graphic'][5]['tweetslist'];
    //        //                 
    //        //                 for (let i in list) {
    //        //                     for (let y in  list[i]['series']) {
    //        //                         elem = [list[i]['name'], list[i]['series'][y]['name'], list[i]['series'][y]['value']];
    //        //                         bodyTable.push(elem);
    //        //                     }
    //        //                 }
    //        // 
    //        //                 doc.autoTable({
    //        //                     startY: hl + 5,
    //        //                     margin: {left: 90},
    //        //                     showHead: false,
    //        //                     bodyStyles: {
    //        //                         fillColor: [52, 73, 94],
    //        //                         textColor: 240
    //        //                     },
    //        //                     alternateRowStyles: {
    //        //                         fillColor: [74, 96, 117]
    //        //                     },
    //        //                     head: [
    //        //                         ['Period', 'Type', 'Value'],
    //        //                     ],
    //        //                     body: bodyTable,
    //        //                 });
    //        //             }
    //        // 
    //        //             hl = hl + 70;
    //        // 
    //        //             // Resume
    //        //             moduleHeight = 70;
    //        // 
    //        //             // Validate pageHeight
    //        //             if ( hl + moduleHeight > pageHeight) {
    //        //                 doc.addPage();
    //        //                 hl = 20;
    //        //             }
    //        // 
    //        //             var svg = this.nbCardContainer.nativeElement.querySelector('#divTwitterResume');
    //        //             var svg2 = svg.children[0].children[0].children[1].children[0].children[0].children[0].children[0].children[0];
    //        //             // await html2canvas(svg.children[0], { 
    //        //             await html2canvas(svg2, { 
    //        //                 // scale: 1,
    //        //                 useCORS: true, 
    //        //                 // foreignObjectRendering: true,  // Render with the background but only if the div is in the screen
    //        //                 // logging: false,
    //        //                 backgroundColor: '#888888',
    //        //                 allowTaint: true,
    //        //                 // removeContainer: false
    //        //                 })
    //        //                 .then(function (canvas) { 
    //        //                     doc.addImage(canvas.toDataURL('image/png'), 'JPEG', 10, hl, 75, 55);
    //        //                 });
    //        // 
    //        //             // Information table
    //        //             if (this.gathered['twitter']['result'][4]['graphic'][0]['resume']['children']) {
    //        //                 let headTable = [];
    //        //                 let bodyTable = [];
    //        //                 let elem = [];
    //        //                 let i: any;
    //        //                 let list = this.gathered['twitter']['result'][4]['graphic'][0]['resume']['children'];
    //        //                 
    //        //                 for (let i in list) {
    //        //                     elem = [list[i]['name'], list[i]['value']];
    //        //                     bodyTable.push(elem);
    //        //                 }
    //        // 
    //        //                 doc.autoTable({
    //        //                     startY: hl + 5,
    //        //                     margin: {left: 90},
    //        //                     showHead: false,
    //        //                     bodyStyles: {
    //        //                         fillColor: [52, 73, 94],
    //        //                         textColor: 240
    //        //                     },
    //        //                     alternateRowStyles: {
    //        //                         fillColor: [74, 96, 117]
    //        //                     },
    //        //                     head: [
    //        //                         ['Name', 'Value'],
    //        //                     ],
    //        //                     body: bodyTable,
    //        //                 });
    //        //             }
    //        // 
    //        //             hl = hl + 70;
    //        // 
    //        //             // Popularity
    //        //             moduleHeight = 70;
    //        // 
    //        //             // Validate pageHeight
    //        //             if ( hl + moduleHeight > pageHeight) {
    //        //                 doc.addPage();
    //        //                 hl = 20;
    //        //             }
    //        // 
    //        //             var svg = this.nbCardContainer.nativeElement.querySelector('#divTwitterPopularity');
    //        //             var svg2 = svg.children[0].children[0].children[1].children[0].children[0].children[0].children[0].children[0];
    //        //             // await html2canvas(svg.children[0], { 
    //        //             await html2canvas(svg2, { 
    //        //                 // scale: 1,
    //        //                 useCORS: true, 
    //        //                 // foreignObjectRendering: true,  // Render with the background but only if the div is in the screen
    //        //                 // logging: false,
    //        //                 backgroundColor: '#888888',
    //        //                 allowTaint: true,
    //        //                 // removeContainer: false
    //        //                 })
    //        //                 .then(function (canvas) { 
    //        //                     doc.addImage(canvas.toDataURL('image/png'), 'JPEG', 10, hl, 75, 55);
    //        //                 });
    //        // 
    //        //             // Information table
    //        //             if (this.gathered['twitter']['result'][4]['graphic'][1]['popularity']) {
    //        //                 let headTable = [];
    //        //                 let bodyTable = [];
    //        //                 let elem = [];
    //        //                 let i: any;
    //        //                 let list = this.gathered['twitter']['result'][4]['graphic'][1]['popularity'];
    //        //                 
    //        //                 for (let i in list) {
    //        //                     elem = [list[i]['name'], list[i]['value']];
    //        //                     bodyTable.push(elem);
    //        //                 }
    //        // 
    //        //                 doc.autoTable({
    //        //                     startY: hl + 5,
    //        //                     margin: {left: 90},
    //        //                     showHead: false,
    //        //                     bodyStyles: {
    //        //                         fillColor: [52, 73, 94],
    //        //                         textColor: 240
    //        //                     },
    //        //                     alternateRowStyles: {
    //        //                         fillColor: [74, 96, 117]
    //        //                     },
    //        //                     head: [
    //        //                         ['Name', 'Value'],
    //        //                     ],
    //        //                     body: bodyTable,
    //        //                 });
    //        //             }
    //        // 
    //        //             hl = hl + 70;
    //        // 
    //        //             // Approval
    //        //             moduleHeight = 70;
    //        // 
    //        //             // Validate pageHeight
    //        //             if ( hl + moduleHeight > pageHeight) {
    //        //                 doc.addPage();
    //        //                 hl = 20;
    //        //             }
    //        // 
    //        //             var svg = this.nbCardContainer.nativeElement.querySelector('#divTwitterApproval');
    //        //             var svg2 = svg.children[0].children[0].children[1].children[0].children[0].children[0].children[0].children[0];
    //        //             // await html2canvas(svg.children[0], { 
    //        //             await html2canvas(svg2, { 
    //        //                 // scale: 1,
    //        //                 useCORS: true, 
    //        //                 // foreignObjectRendering: true,  // Render with the background but only if the div is in the screen
    //        //                 // logging: false,
    //        //                 backgroundColor: '#888888',
    //        //                 allowTaint: true,
    //        //                 // removeContainer: false
    //        //                 })
    //        //                 .then(function (canvas) { 
    //        //                     doc.addImage(canvas.toDataURL('image/png'), 'JPEG', 10, hl, 75, 55);
    //        //                 });
    //        // 
    //        //             // Information table
    //        //             if (this.gathered['twitter']['result'][4]['graphic'][2]['approval']) {
    //        //                 let headTable = [];
    //        //                 let bodyTable = [];
    //        //                 let elem = [];
    //        //                 let i: any;
    //        //                 let list = this.gathered['twitter']['result'][4]['graphic'][2]['approval'];
    //        //                 
    //        //                 for (let i in list) {
    //        //                     elem = [list[i]['name'], list[i]['value']];
    //        //                     bodyTable.push(elem);
    //        //                 }
    //        // 
    //        //                 doc.autoTable({
    //        //                     startY: hl + 5,
    //        //                     margin: {left: 90},
    //        //                     showHead: false,
    //        //                     bodyStyles: {
    //        //                         fillColor: [52, 73, 94],
    //        //                         textColor: 240
    //        //                     },
    //        //                     alternateRowStyles: {
    //        //                         fillColor: [74, 96, 117]
    //        //                     },
    //        //                     head: [
    //        //                         ['Name', 'Value'],
    //        //                     ],
    //        //                     body: bodyTable,
    //        //                 });
    //        //             }
    //        // 
    //        //             hl = hl + 70;
    //        // 
    //        //             // Hashtag
    //        //             moduleHeight = 70;
    //        // 
    //        //             // Validate pageHeight
    //        //             if ( hl + moduleHeight > pageHeight) {
    //        //                 doc.addPage();
    //        //                 hl = 20;
    //        //             }
    //        // 
    //        //             var svg = this.nbCardContainer.nativeElement.querySelector('#divTwitterHashtag');
    //        //             var svg2 = svg.children[0].children[0].children[1].children[0].children[0].children[0];
    //        //             // await html2canvas(svg.children[0], { 
    //        //             await html2canvas(svg2, { 
    //        //                 // scale: 1,
    //        //                 useCORS: true, 
    //        //                 // foreignObjectRendering: true,  // Render with the background but only if the div is in the screen
    //        //                 // logging: false,
    //        //                 backgroundColor: '#333333',
    //        //                 allowTaint: true,
    //        //                 // removeContainer: false
    //        //                 })
    //        //                 .then(function (canvas) { 
    //        //                     doc.addImage(canvas.toDataURL('image/png'), 'JPEG', 10, hl, 75, 55);
    //        //                 });
    //        // 
    //        //             // Information table
    //        //             if (this.gathered['twitter']['result'][4]['graphic'][3]['hashtag']) {
    //        //                 let headTable = [];
    //        //                 let bodyTable = [];
    //        //                 let elem = '';
    //        //                 let i: any;
    //        //                 let list = this.gathered['twitter']['result'][4]['graphic'][3]['hashtag'];
    //        //                 
    //        //                 for (let i in list) {
    //        //                     elem = elem + list[i]['label'] + ' ';
    //        //                 }
    //        //                 bodyTable.push([elem]);
    //        // 
    //        //                 doc.autoTable({
    //        //                     startY: hl + 5,
    //        //                     margin: {left: 90},
    //        //                     showHead: true,
    //        //                     styles: { overflow: 'linebreak', cellWidth: 'wrap', halign: 'center' },
    //        //                     columnStyles: { 0: { cellWidth: 'auto' } },
    //        //                     bodyStyles: {
    //        //                         fillColor: [52, 73, 94],
    //        //                         textColor: 240
    //        //                     },
    //        //                     alternateRowStyles: {
    //        //                         fillColor: [74, 96, 117]
    //        //                     },
    //        //                     head: [
    //        //                         ['Hashtags'],
    //        //                     ],
    //        //                     body: bodyTable,
    //        //                 });
    //        //             }
    //        // 
    //        //             hl = hl + 70;
    //        // 
    //        //             // Mentions
    //        //             moduleHeight = 70;
    //        // 
    //        //             // Validate pageHeight
    //        //             if ( hl + moduleHeight > pageHeight) {
    //        //                 doc.addPage();
    //        //                 hl = 20;
    //        //             }
    //        // 
    //        //             var svg = this.nbCardContainer.nativeElement.querySelector('#divTwitterUsers');
    //        //             var svg2 = svg.children[0].children[0].children[1].children[0].children[0].children[0];
    //        //             // await html2canvas(svg.children[0], { 
    //        //             await html2canvas(svg2, { 
    //        //                 // scale: 1,
    //        //                 useCORS: true, 
    //        //                 // foreignObjectRendering: true,  // Render with the background but only if the div is in the screen
    //        //                 // logging: false,
    //        //                 backgroundColor: '#333333',
    //        //                 allowTaint: true,
    //        //                 // removeContainer: false
    //        //                 })
    //        //                 .then(function (canvas) { 
    //        //                     doc.addImage(canvas.toDataURL('image/png'), 'JPEG', 10, hl, 75, 55);
    //        //                 });
    //        // 
    //        //             // Information table
    //        //             if (this.gathered['twitter']['result'][4]['graphic'][4]['users']) {
    //        //                 let headTable = [];
    //        //                 let bodyTable = [];
    //        //                 let elem = '';
    //        //                 let i: any;
    //        //                 let list = this.gathered['twitter']['result'][4]['graphic'][4]['users'];
    //        //                 
    //        //                 for (let i in list) {
    //        //                     elem = elem + list[i]['title'] + ' ';
    //        //                 }
    //        //                 bodyTable.push([elem]);
    //        // 
    //        //                 doc.autoTable({
    //        //                     startY: hl,
    //        //                     margin: {left: 90},
    //        //                     showHead: true,
    //        //                     styles: { overflow: 'linebreak', cellWidth: 'wrap', halign: 'center' },
    //        //                     columnStyles: { 0: { cellWidth: 'auto' } },
    //        //                     bodyStyles: {
    //        //                         fillColor: [52, 73, 94],
    //        //                         textColor: 240
    //        //                     },
    //        //                     alternateRowStyles: {
    //        //                         fillColor: [74, 96, 117]
    //        //                     },
    //        //                     head: [
    //        //                         ['Mentions to users'],
    //        //                     ],
    //        //                     body: bodyTable,
    //        //                 });
    //        //             }
    //        // 
    //        //             if (doc.previousAutoTable.finalY > hl + 70) {
    //        //                 hl = doc.previousAutoTable.finalY
    //        //             }
    //        //             else {
    //        //                 hl = hl + 70;
    //        //             }
    //        //         }
    //        // 
    //        //         hl = hl + 5; // Space between modules
    //        // 
    //        // 
    //        //         // Instagram module report
    //        //         if (this.gathered['instagram'] && this.gathered['instagram']['result'] && 
    //        //                 this.gathered['instagram']['result'].length > 3) {
    //        //             moduleHeight = 80;
    //        // 
    //        //             // Validate pageHeight
    //        //             if ( hl + moduleHeight > pageHeight) {
    //        //                 doc.addPage();
    //        //                 hl = 20;
    //        //             }
    //        // 
    //        //             // EmailRep
    //        //             doc.setFontSize(11);
    //        //             doc.setDrawColor(44, 93, 126);
    //        //             doc.setFillColor(44, 93, 126);
    //        //             doc.rect(10, hl, 190, 7, 'F');
    //        //             doc.setTextColor(255, 255, 255);
    //        //             doc.text('Module Instagram', 105, hl + 5, null, null, 'center');
    //        //             hl = hl + 10;
    //        // 
    //        //             var svg = this.nbCardContainer.nativeElement.querySelector('#divInstagramSocial');
    //        //             var svg2 = svg.children[0].children[0].children[1].children[0].children[0].children[0];
    //        //             await html2canvas(svg2, { 
    //        //                 // scale: 1,
    //        //                 useCORS: true, 
    //        //                 // foreignObjectRendering: true,  // Render with the background but only if the div is in the screen
    //        //                 // logging: false,
    //        //                 backgroundColor: '#333333',
    //        //                 allowTaint: true,
    //        //                 // removeContainer: false
    //        //                 })
    //        //                 .then(function (canvas) { 
    //        //                     doc.addImage(canvas.toDataURL('image/png'), 'JPEG', 10, hl, 75, 55);
    //        //                 });
    //        // 
    //        //             doc.setFontSize(11);
    //        //             doc.setFont('helvetica', 'normal');
    //        //             doc.setTextColor(79, 79, 79);
    //        //             infoText = 'The information of the chart is shown in the following table.';
    //        //             var splitText = doc.splitTextToSize(infoText, 110);
    //        //             var y = 6;
    //        //             for (var i=0; i<splitText.length; i++){
    //        //                 doc.text(90, hl + y, splitText[i]);
    //        //                 y = y + 4;
    //        //             }
    //        // 
    //        //             // Information table
    //        //             if (this.gathered['instagram']['result'][4]['graphic'][0]['instagram']) {
    //        //                 let headTable = [];
    //        //                 let bodyTable = [];
    //        //                 let elem = [];
    //        //                 let i: any;
    //        //                 let list = this.gathered['instagram']['result'][4]['graphic'][0]['instagram'];
    //        //                 
    //        //                 for (let i in list) {
    //        //                     if (list[i]['title'] != 'Instagram') {
    //        //                         elem = [list[i]['title'], list[i]['subtitle']];
    //        //                         bodyTable.push(elem);
    //        //                     }
    //        //                 }
    //        // 
    //        //                 doc.autoTable({
    //        //                     startY: hl + 11,
    //        //                     margin: {left: 90},
    //        //                     showHead: false,
    //        //                     styles: { overflow: 'hidden' },
    //        //                     bodyStyles: {
    //        //                         fillColor: [52, 73, 94],
    //        //                         textColor: 240
    //        //                     },
    //        //                     alternateRowStyles: {
    //        //                         fillColor: [74, 96, 117]
    //        //                     },
    //        //                     head: [
    //        //                         ['Name', 'Value'],
    //        //                     ],
    //        //                     body: bodyTable,
    //        //                 });
    //        // 
    //        //                 let finalY = doc.previousAutoTable.finalY;
    //        //                 doc.autoTable({
    //        //                     startY: finalY,
    //        //                     // html: '.table',
    //        //                     useCss: true,
    //        //                 });
    //        //         
    //        //                 hl = finalY
    //        //             }
    //        // 
    //        //             hl = hl + 10;
    //        // 
    //        //             var svg = this.nbCardContainer.nativeElement.querySelector('#divInstagramPosts');
    //        //             var svg2 = svg.children[0].children[0].children[1].children[0].children[0].children[0];
    //        //             await html2canvas(svg2, { 
    //        //                 // scale: 1,
    //        //                 useCORS: true, 
    //        //                 // foreignObjectRendering: true,  // Render with the background but only if the div is in the screen
    //        //                 // logging: false,
    //        //                 backgroundColor: '#333333',
    //        //                 allowTaint: true,
    //        //                 // removeContainer: false
    //        //                 })
    //        //                 .then(function (canvas) { 
    //        //                     doc.addImage(canvas.toDataURL('image/png'), 'JPEG', 10, hl, 75, 55);
    //        //                 });
    //        // 
    //        //             doc.setFontSize(11);
    //        //             doc.setFont('helvetica', 'normal');
    //        //             doc.setTextColor(79, 79, 79);
    //        //             infoText = 'The information of the chart is shown in the following table.';
    //        //             var splitText = doc.splitTextToSize(infoText, 110);
    //        //             var y = 6;
    //        //             for (var i=0; i<splitText.length; i++){
    //        //                 doc.text(90, hl + y, splitText[i]);
    //        //                 y = y + 4;
    //        //             }
    //        // 
    //        //             // Information table
    //        //             if (this.gathered['instagram']['result'][4]['graphic'][1]['postslist']) {
    //        //                 let headTable = [];
    //        //                 let bodyTable = [];
    //        //                 let elem = [];
    //        //                 let i: any;
    //        //                 let list = this.gathered['instagram']['result'][4]['graphic'][1]['postslist'];
    //        //                 
    //        //                 for (let i in list) {
    //        //                     // if (list[i]['title'] != 'EmailRep') {
    //        //                         elem = [list[i]['name'], list[i]['series'][0]['value'], list[i]['series'][1]['value']];
    //        //                         bodyTable.push(elem);
    //        //                     // }
    //        //                 }
    //        // 
    //        //                 doc.autoTable({
    //        //                     startY: hl + 11,
    //        //                     margin: {left: 90},
    //        //                     showHead: true,
    //        //                     styles: { overflow: 'hidden' },
    //        //                     bodyStyles: {
    //        //                         fillColor: [52, 73, 94],
    //        //                         textColor: 240
    //        //                     },
    //        //                     alternateRowStyles: {
    //        //                         fillColor: [74, 96, 117]
    //        //                     },
    //        //                     head: [
    //        //                         ['Post', 'Comments', 'Likes'],
    //        //                     ],
    //        //                     body: bodyTable,
    //        //                 });
    //        // 
    //        //                 let finalY = doc.previousAutoTable.finalY;
    //        //                 doc.autoTable({
    //        //                     startY: finalY,
    //        //                     // html: '.table',
    //        //                     useCss: true,
    //        //                 });
    //        //         
    //        //                 hl = finalY
    //        //             }
    //        // 
    //        //             hl = hl + 10;
    //        //         }
    //        // 
    //        // 
    //        //         // Github module report
    //        //         if (this.gathered['github'] && this.gathered['github']['result'] &&
    //        //                 this.gathered['github']['result'].length > 3) {
    //        // 
    //        //             // Resume
    //        //             moduleHeight = 80;
    //        // 
    //        //             // Validate pageHeight
    //        //             if ( hl + moduleHeight > pageHeight) {
    //        //                 doc.addPage();
    //        //                 hl = 20;
    //        //             }
    //        // 
    //        //             doc.setFontSize(11);
    //        //             doc.setDrawColor(44, 93, 126);
    //        //             doc.setFillColor(44, 93, 126);
    //        //             doc.rect(10, hl, 190, 7, 'F');
    //        //             doc.setTextColor(255, 255, 255);
    //        //             doc.text('Module github', 105, hl + 5, null, null, 'center');
    //        //             hl = hl + 10;
    //        // 
    //        //             var svg = this.nbCardContainer.nativeElement.querySelector('#divGithubGraphs');
    //        //             var svg2 = svg.children[0].children[0].children[1].children[0].children[0].children[0];
    //        //             // await html2canvas(svg.children[0], { 
    //        //             await html2canvas(svg2, { 
    //        //                 // scale: 1,
    //        //                 useCORS: true, 
    //        //                 // foreignObjectRendering: true,  // Render with the background but only if the div is in the screen
    //        //                 // logging: false,
    //        //                 backgroundColor: '#333333',
    //        //                 allowTaint: true,
    //        //                 // removeContainer: false
    //        //                 })
    //        //                 .then(function (canvas) { 
    //        //                     doc.addImage(canvas.toDataURL('image/png'), 'JPEG', 10, hl, 75, 55);
    //        //                 });
    //        // 
    //        //             doc.setFontSize(11);
    //        //             doc.setFont('helvetica', 'normal');
    //        //             doc.setTextColor(79, 79, 79);
    //        //             infoText = 'The information of the chart is shown in the following table.';
    //        //             var splitText = doc.splitTextToSize(infoText, 110);
    //        //             var y = 6;
    //        //             for (var i=0; i<splitText.length; i++){
    //        //                 doc.text(90, hl + y, splitText[i]);
    //        //                 y = y + 4;
    //        //             }
    //        // 
    //        //             // Information table
    //        //             if (this.gathered['github']['result'][4]['graphic'][0]['github']) {
    //        //                 let headTable = [];
    //        //                 let bodyTable = [];
    //        //                 let elem = [];
    //        //                 let i: any;
    //        //                 let list = this.gathered['github']['result'][4]['graphic'][0]['github'];
    //        //                 
    //        //                 for (let i in list) {
    //        //                     if (list[i]['title'] != 'Github' && list[i]['subtitle']) {
    //        //                         elem = [list[i]['title'], list[i]['subtitle']];
    //        //                         bodyTable.push(elem);
    //        //                     }
    //        //                 }
    //        // 
    //        //                 doc.autoTable({
    //        //                     startY: hl + 11,
    //        //                     margin: {left: 90},
    //        //                     showHead: false,
    //        //                     bodyStyles: {
    //        //                         fillColor: [52, 73, 94],
    //        //                         textColor: 240
    //        //                     },
    //        //                     alternateRowStyles: {
    //        //                         fillColor: [74, 96, 117]
    //        //                     },
    //        //                     head: [
    //        //                         ['Name', 'Value'],
    //        //                     ],
    //        //                     body: bodyTable,
    //        //                 });
    //        //             }
    //        // 
    //        //             hl = hl + 70;
    //        // 
    //        //             // Github Calendar
    //        //             moduleHeight = 70;
    //        // 
    //        //             // Validate pageHeight
    //        //             if ( hl + moduleHeight > pageHeight) {
    //        //                 doc.addPage();
    //        //                 hl = 20;
    //        //             }
    //        // 
    //        //             var svg = this.nbCardContainer.nativeElement.querySelector('#divGithubCalendar');
    //        //             var svg2 = svg.children[0].children[0].children[1].children[0].children[0].children[0];
    //        //             // await html2canvas(svg.children[0], { 
    //        //             await html2canvas(svg2, { 
    //        //                 // scale: 1,
    //        //                 useCORS: true, 
    //        //                 // foreignObjectRendering: true,  // Render with the background but only if the div is in the screen
    //        //                 // logging: false,
    //        //                 backgroundColor: '#333333',
    //        //                 allowTaint: true,
    //        //                 // removeContainer: false
    //        //                 })
    //        //                 .then(function (canvas) { 
    //        //                     doc.addImage(canvas.toDataURL('image/png'), 'JPEG', 30, hl, 150, 35);
    //        //                 });
    //        // 
    //        //             // var svg = this.nbCardContainer.nativeElement.querySelector('#divGithubCalendar');
    //        //             // await html2canvas(svg.children[0], { 
    //        //             //     scale: 1,
    //        //             //     useCORS: true, 
    //        //             //     // foreignObjectRendering: true,  // Render with the background but only if the div is in the screen
    //        //             //     logging: true,
    //        //             //     backgroundColor: '#51A5D7',
    //        //             //     allowTaint: true,
    //        //             //     removeContainer: true
    //        //             //     })
    //        //             //     .then(function (canvas) { 
    //        //             //         doc.addImage(canvas.toDataURL('image/png'), 'JPEG', 30, hl, 150, 65);
    //        //             //     });
    //        // 
    //        //             hl = hl + 70;
    //        // 
    //        //         }
    //        // 
    //        //         hl = hl + 5; // Space between modules
    //        // 
    //        //         // Linkedin module report   TODO Add conditions of inexistence or empty
    //        //         if (this.gathered['linkedin'] && this.gathered['linkedin']['result'] && 
    //        //                 this.gathered['linkedin']['result'].length > 3) {
    //        //             moduleHeight = 80;
    //        // 
    //        //             // Validate pageHeight
    //        //             if ( hl + moduleHeight > pageHeight) {
    //        //                 doc.addPage();
    //        //                 hl = 20;
    //        //             }
    //        // 
    //        //             // Linkedin Social
    //        //             doc.setFontSize(11);
    //        //             doc.setDrawColor(44, 93, 126);
    //        //             doc.setFillColor(44, 93, 126);
    //        //             doc.rect(10, hl, 190, 7, 'F');
    //        //             doc.setTextColor(255, 255, 255);
    //        //             doc.text('Module linkedin', 105, hl + 5, null, null, 'center');
    //        //             hl = hl + 10;
    //        // 
    //        //             var svg = this.nbCardContainer.nativeElement.querySelector('#divLinkedinGraphs');
    //        //             var svg2 = svg.children[0].children[0].children[1].children[0].children[0].children[0];
    //        //             // await html2canvas(svg.children[0], { 
    //        //             await html2canvas(svg2, { 
    //        //                 // scale: 1,
    //        //                 useCORS: true, 
    //        //                 // foreignObjectRendering: true,  // Render with the background but only if the div is in the screen
    //        //                 // logging: false,
    //        //                 backgroundColor: '#333333',
    //        //                 allowTaint: true,
    //        //                 // removeContainer: false
    //        //                 })
    //        //                 .then(function (canvas) { 
    //        //                     doc.addImage(canvas.toDataURL('image/png'), 'JPEG', 10, hl, 75, 55);
    //        //                 });
    //        // 
    //        //             doc.setFontSize(11);
    //        //             doc.setFont('helvetica', 'normal');
    //        //             doc.setTextColor(79, 79, 79);
    //        //             infoText = 'The information of the chart is shown in the following table.';
    //        //             var splitText = doc.splitTextToSize(infoText, 110);
    //        //             var y = 6;
    //        //             for (var i=0; i<splitText.length; i++){
    //        //                 doc.text(90, hl + y, splitText[i]);
    //        //                 y = y + 4;
    //        //             }
    //        // 
    //        //             // Information table
    //        //             if (this.gathered['linkedin']['result'][4]['graphic'][0]['social']) {
    //        //                 let headTable = [];
    //        //                 let bodyTable = [];
    //        //                 let elem = [];
    //        //                 let i: any;
    //        //                 let list = this.gathered['linkedin']['result'][4]['graphic'][0]['social'];
    //        //                 
    //        //                 for (let i in list) {
    //        //                     if (list[i]['title'] != 'Linkedin' && list[i]['subtitle']) {
    //        //                         elem = [list[i]['title'], list[i]['subtitle']];
    //        //                         bodyTable.push(elem);
    //        //                     }
    //        //                 }
    //        // 
    //        //                 doc.autoTable({
    //        //                     startY: hl + 11,
    //        //                     margin: {left: 90},
    //        //                     showHead: false,
    //        //                     styles: { overflow: 'hidden' },
    //        //                     bodyStyles: {
    //        //                         fillColor: [52, 73, 94],
    //        //                         textColor: 240
    //        //                     },
    //        //                     alternateRowStyles: {
    //        //                         fillColor: [74, 96, 117]
    //        //                     },
    //        //                     head: [
    //        //                         ['Name', 'Value'],
    //        //                     ],
    //        //                     body: bodyTable,
    //        //                 });
    //        //             }
    //        // 
    //        //             hl = hl + 70;
    //        // 
    //        //             // Linkedin Skill
    //        //             moduleHeight = 80;
    //        // 
    //        //             // Validate pageHeight
    //        //             if ( hl + moduleHeight > pageHeight) {
    //        //                 doc.addPage();
    //        //                 hl = 20;
    //        //             }
    //        // 
    //        //             var svg = this.nbCardContainer.nativeElement.querySelector('#divLinkedinBubble');
    //        //             var svg2 = svg.children[0].children[0].children[1].children[0].children[0].children[0];
    //        //             // await html2canvas(svg.children[0], { 
    //        //             await html2canvas(svg2, { 
    //        //                 // scale: 1,
    //        //                 useCORS: true, 
    //        //                 // foreignObjectRendering: true,  // Render with the background but only if the div is in the screen
    //        //                 // logging: false,
    //        //                 backgroundColor: '#333333',
    //        //                 allowTaint: true,
    //        //                 // removeContainer: false
    //        //                 })
    //        //                 .then(function (canvas) { 
    //        //                     doc.addImage(canvas.toDataURL('image/png'), 'JPEG', 10, hl, 75, 55);
    //        //                 });
    //        // 
    //        //             doc.setFontSize(11);
    //        //             doc.setFont('helvetica', 'normal');
    //        //             doc.setTextColor(79, 79, 79);
    //        //             infoText = 'Principal skill.';
    //        //             var splitText = doc.splitTextToSize(infoText, 110);
    //        //             var y = 6;
    //        //             for (var i=0; i<splitText.length; i++){
    //        //                 doc.text(90, hl + y, splitText[i]);
    //        //                 y = y + 4;
    //        //             }
    //        // 
    //        //             // Information table
    //        //             if (this.gathered['linkedin']['result'][4]['graphic'][1]['skills']['children']) {
    //        //                 let headTable = [];
    //        //                 let bodyTable = [];
    //        //                 let elem = [];
    //        //                 let i: any;
    //        //                 let list = this.gathered['linkedin']['result'][4]['graphic'][1]['skills']['children'];
    //        //                 
    //        //                 for (let i in list) {
    //        //                     if (Number(i) < 6) {
    //        //                         elem = [list[i]['name'], list[i]['value']];
    //        //                         bodyTable.push(elem);
    //        //                     }
    //        //                 }
    //        // 
    //        //                 doc.autoTable({
    //        //                     startY: hl + 11,
    //        //                     margin: {left: 90},
    //        //                     showHead: false,
    //        //                     styles: { overflow: 'hidden' },
    //        //                     bodyStyles: {
    //        //                         fillColor: [52, 73, 94],
    //        //                         textColor: 240
    //        //                     },
    //        //                     alternateRowStyles: {
    //        //                         fillColor: [74, 96, 117]
    //        //                     },
    //        //                     head: [
    //        //                         ['Skill', 'Value'],
    //        //                     ],
    //        //                     body: bodyTable,
    //        //                 });
    //        //             }
    //        // 
    //        //             hl = hl + 70;
    //        // 
    //        //             // Information table Certifications
    //        //             if (this.gathered['linkedin']['result'][4]['graphic'][2]['certificationView']) {
    //        //                 let headTable = [];
    //        //                 let bodyTable = [];
    //        //                 let elem = [];
    //        //                 let i: any;
    //        //                 let list = this.gathered['linkedin']['result'][4]['graphic'][2]['certificationView'];
    //        //                 
    //        //                 for (let i in list) {
    //        //                     elem = [list[i]['name'], list[i]['desc']];
    //        //                     bodyTable.push(elem);
    //        //                 }
    //        //         
    //        //                 headTable = [['title']]
    //        //                 headTable[0][0] = {content: 'Certifications', colSpan: 2, styles: {halign: 'center', fillColor: [22, 160, 133]}};
    //        //                 doc.autoTable({
    //        //                     startY: hl,
    //        //                     head: headTable, 
    //        //                     body: bodyTable,
    //        //                 });
    //        //             
    //        //                 let finalY = doc.previousAutoTable.finalY;
    //        //         
    //        //                 hl = finalY
    //        //             }
    //        //             // Information table Positions
    //        //             if (this.gathered['linkedin']['result'][4]['graphic'][3]['positionGroupView']) {
    //        //                 let headTable = [];
    //        //                 let bodyTable = [];
    //        //                 let elem = [];
    //        //                 let i: any;
    //        //                 let list = this.gathered['linkedin']['result'][4]['graphic'][3]['positionGroupView'];
    //        //                 
    //        //                 for (let i in list) {
    //        //                     elem = [list[i]['label']];
    //        //                     bodyTable.push(elem);
    //        //                 }
    //        //         
    //        //                 headTable = [['title']]
    //        //                 headTable[0][0] = {content: 'Positions', colSpan: 1, styles: {halign: 'center', fillColor: [22, 160, 133]}};
    //        //                 doc.autoTable({
    //        //                     startY: hl + 4,
    //        //                     head: headTable, 
    //        //                     body: bodyTable,
    //        //                     margin: 40,
    //        //                 });
    //        //             
    //        //                 let finalY = doc.previousAutoTable.finalY;
    //        //         
    //        //                 hl = finalY
    //        //             }
    //        //         }
    //        // 
    //        //         hl = hl + 10; // Space between modules
    //        // 
    //        //         // Keybase module report
    //        //         if (this.gathered['keybase'] && this.gathered['keybase']['result'] &&
    //        //                this.gathered['keybase']['result'].length > 3) {
    //        //             moduleHeight = 80;
    //        // 
    //        //             // Validate pageHeight
    //        //             if ( hl + moduleHeight > pageHeight) {
    //        //                 doc.addPage();
    //        //                 hl = 20;
    //        //             }
    //        // 
    //        //             // Keybase Social
    //        //             doc.setFontSize(11);
    //        //             doc.setDrawColor(44, 93, 126);
    //        //             doc.setFillColor(44, 93, 126);
    //        //             doc.rect(10, hl, 190, 7, 'F');
    //        //             doc.setTextColor(255, 255, 255);
    //        //             doc.text('Module keybase', 105, hl + 5, null, null, 'center');
    //        //             hl = hl + 10;
    //        // 
    //        //             var svg = this.nbCardContainer.nativeElement.querySelector('#divKeybaseSocial');
    //        //             var svg2 = svg.children[0].children[0].children[1].children[0].children[0].children[0];
    //        //             // await html2canvas(svg.children[0], { 
    //        //             await html2canvas(svg2, { 
    //        //                 // scale: 1,
    //        //                 useCORS: true, 
    //        //                 // foreignObjectRendering: true,  // Render with the background but only if the div is in the screen
    //        //                 // logging: false,
    //        //                 backgroundColor: '#333333',
    //        //                 allowTaint: true,
    //        //                 // removeContainer: false
    //        //                 })
    //        //                 .then(function (canvas) { 
    //        //                     doc.addImage(canvas.toDataURL('image/png'), 'JPEG', 10, hl, 75, 55);
    //        //                 });
    //        // 
    //        //             doc.setFontSize(11);
    //        //             doc.setFont('helvetica', 'normal');
    //        //             doc.setTextColor(79, 79, 79);
    //        //             infoText = 'The information of the chart is shown in the following table.';
    //        //             var splitText = doc.splitTextToSize(infoText, 110);
    //        //             var y = 6;
    //        //             for (var i=0; i<splitText.length; i++){
    //        //                 doc.text(90, hl + y, splitText[i]);
    //        //                 y = y + 4;
    //        //             }
    //        // 
    //        //             // Information table
    //        //             if (this.gathered['keybase']['result'][4]['graphic'][0]['keysocial']) {
    //        //                 let headTable = [];
    //        //                 let bodyTable = [];
    //        //                 let elem = [];
    //        //                 let i: any;
    //        //                 let list = this.gathered['keybase']['result'][4]['graphic'][0]['keysocial'];
    //        //                 
    //        //                 for (let i in list) {
    //        //                     if (list[i]['title'] != 'KeybaseSocial' && list[i]['subtitle']) {
    //        //                         if (Number(i) < 8) {
    //        //                             elem = [list[i]['title'], list[i]['subtitle']];
    //        //                             bodyTable.push(elem);
    //        //                         }
    //        //                     }
    //        //                 }
    //        // 
    //        //                 doc.autoTable({
    //        //                     startY: hl + 11,
    //        //                     margin: {left: 90},
    //        //                     showHead: false,
    //        //                     styles: { overflow: 'hidden' },
    //        //                     bodyStyles: {
    //        //                         fillColor: [52, 73, 94],
    //        //                         textColor: 240
    //        //                     },
    //        //                     alternateRowStyles: {
    //        //                         fillColor: [74, 96, 117]
    //        //                     },
    //        //                     head: [
    //        //                         ['Name', 'Value'],
    //        //                     ],
    //        //                     body: bodyTable,
    //        //                 });
    //        //             }
    //        // 
    //        //             hl = hl + 70;
    //        // 
    //        //             // Keybase Device
    //        //             moduleHeight = 80;
    //        // 
    //        //             // Validate pageHeight
    //        //             if ( hl + moduleHeight > pageHeight) {
    //        //                 doc.addPage();
    //        //                 hl = 20;
    //        //             }
    //        // 
    //        //             var svg = this.nbCardContainer.nativeElement.querySelector('#divKeybaseDevices');
    //        //             var svg2 = svg.children[0].children[0].children[1].children[0].children[0].children[0];
    //        //             // await html2canvas(svg.children[0], { 
    //        //             await html2canvas(svg2, { 
    //        //                 // scale: 1,
    //        //                 useCORS: true, 
    //        //                 // foreignObjectRendering: true,  // Render with the background but only if the div is in the screen
    //        //                 // logging: false,
    //        //                 backgroundColor: '#333333',
    //        //                 allowTaint: true,
    //        //                 // removeContainer: false
    //        //                 })
    //        //                 .then(function (canvas) { 
    //        //                     doc.addImage(canvas.toDataURL('image/png'), 'JPEG', 10, hl, 75, 55);
    //        //                 });
    //        // 
    //        //             doc.setFontSize(11);
    //        //             doc.setFont('helvetica', 'normal');
    //        //             doc.setTextColor(79, 79, 79);
    //        //             infoText = 'The information of the chart is shown in the following table.';
    //        //             var splitText = doc.splitTextToSize(infoText, 110);
    //        //             var y = 6;
    //        //             for (var i=0; i<splitText.length; i++){
    //        //                 doc.text(90, hl + y, splitText[i]);
    //        //                 y = y + 4;
    //        //             }
    //        // 
    //        //             // Information table
    //        //             if (this.gathered['keybase']['result'][4]['graphic'][1]['devices']) {
    //        //                 let headTable = [];
    //        //                 let bodyTable = [];
    //        //                 let elem = [];
    //        //                 let i: any;
    //        //                 let list = this.gathered['keybase']['result'][4]['graphic'][1]['devices'];
    //        //                 
    //        //                 for (let i in list) {
    //        //                     if (list[i]['title'] != 'Devices' && list[i]['subtitle']) {
    //        //                         if (Number(i) < 8) {
    //        //                             elem = [list[i]['title'], list[i]['subtitle']];
    //        //                             bodyTable.push(elem);
    //        //                         }
    //        //                     }
    //        //                 }
    //        // 
    //        //                 doc.autoTable({
    //        //                     startY: hl + 11,
    //        //                     margin: {left: 90},
    //        //                     showHead: false,
    //        //                     styles: { overflow: 'hidden' },
    //        //                     bodyStyles: {
    //        //                         fillColor: [52, 73, 94],
    //        //                         textColor: 240
    //        //                     },
    //        //                     alternateRowStyles: {
    //        //                         fillColor: [74, 96, 117]
    //        //                     },
    //        //                     head: [
    //        //                         ['Name', 'Value'],
    //        //                     ],
    //        //                     body: bodyTable,
    //        //                 });
    //        //             }
    //        //             hl = hl + 70;
    //        //         }
    //        // 
    //        //         hl = hl + 10; // Space between modules
    //        // 
    //        //         // Leaks module report
    //        //         if (this.gathered['leaks'] && this.gathered['leaks']['result'] &&
    //        //                this.gathered['leaks']['result'].length > 3) {
    //        //             moduleHeight = 80;
    //        // 
    //        //             // Validate pageHeight
    //        //             if ( hl + moduleHeight > pageHeight) {
    //        //                 doc.addPage();
    //        //                 hl = 20;
    //        //             }
    //        // 
    //        //             // Leaks
    //        //             doc.setFontSize(11);
    //        //             doc.setDrawColor(44, 93, 126);
    //        //             doc.setFillColor(44, 93, 126);
    //        //             doc.rect(10, hl, 190, 7, 'F');
    //        //             doc.setTextColor(255, 255, 255);
    //        //             doc.text('Module leaks', 105, hl + 5, null, null, 'center');
    //        //             hl = hl + 10;
    //        // 
    //        //             var svg = this.nbCardContainer.nativeElement.querySelector('#divLeakSocial');
    //        //             var svg2 = svg.children[0].children[0].children[1].children[0].children[0].children[0];
    //        //             // await html2canvas(svg.children[0], { 
    //        //             await html2canvas(svg2, { 
    //        //                 // scale: 1,
    //        //                 useCORS: false, 
    //        //                 // foreignObjectRendering: true,  // Render with the background but only if the div is in the screen
    //        //                 // logging: false,
    //        //                 backgroundColor: '#333333',
    //        //                 allowTaint: true,
    //        //                 // removeContainer: false
    //        //                 })
    //        //                 .then(function (canvas) { 
    //        //                     doc.addImage(canvas.toDataURL('image/png'), 'JPEG', 10, hl, 75, 55);
    //        //                 });
    //        // 
    //        //             doc.setFontSize(11);
    //        //             doc.setFont('helvetica', 'normal');
    //        //             doc.setTextColor(79, 79, 79);
    //        //             infoText = 'The information of the chart is shown in the following table.';
    //        //             var splitText = doc.splitTextToSize(infoText, 110);
    //        //             var y = 6;
    //        //             for (var i=0; i<splitText.length; i++){
    //        //                 doc.text(90, hl + y, splitText[i]);
    //        //                 y = y + 4;
    //        //             }
    //        // 
    //        //             // Information table
    //        //             if (this.gathered['leaks']['result'][4]['graphic'][0]['leaks']) {
    //        //                 let headTable = [];
    //        //                 let bodyTable = [];
    //        //                 let elem = [];
    //        //                 let i: any;
    //        //                 let list = this.gathered['leaks']['result'][4]['graphic'][0]['leaks'];
    //        //                 
    //        //                 for (let i in list) {
    //        //                     if (list[i]['title'] != 'Leaks' && list[i]['subtitle']) {
    //        //                         if (Number(i) < 8) {
    //        //                             elem = [list[i]['title'], list[i]['subtitle']];
    //        //                             bodyTable.push(elem);
    //        //                         }
    //        //                     }
    //        //                 }
    //        // 
    //        //                 doc.autoTable({
    //        //                     startY: hl + 11,
    //        //                     margin: {left: 90},
    //        //                     showHead: false,
    //        //                     styles: { overflow: 'hidden' },
    //        //                     bodyStyles: {
    //        //                         fillColor: [52, 73, 94],
    //        //                         textColor: 240
    //        //                     },
    //        //                     alternateRowStyles: {
    //        //                         fillColor: [74, 96, 117]
    //        //                     },
    //        //                     head: [
    //        //                         ['Leak', 'Breach Date'],
    //        //                     ],
    //        //                     body: bodyTable,
    //        //                 });
    //        //             }
    //        // 
    //        //             hl = hl + 70;
    //        //         }
    //        // 
    //        // 
    //        //         // SocialScan module report
    //        //         if (this.gathered['socialscan'] && this.gathered['socialscan']['result'] && 
    //        //                 this.gathered['socialscan']['result'].length > 3) {
    //        //             moduleHeight = 80;
    //        // 
    //        //             // Validate pageHeight
    //        //             if ( hl + moduleHeight > pageHeight) {
    //        //                 doc.addPage();
    //        //                 hl = 20;
    //        //             }
    //        // 
    //        //             // EmailRep
    //        //             doc.setFontSize(11);
    //        //             doc.setDrawColor(44, 93, 126);
    //        //             doc.setFillColor(44, 93, 126);
    //        //             doc.rect(10, hl, 190, 7, 'F');
    //        //             doc.setTextColor(255, 255, 255);
    //        //             doc.text('Module socialscan', 105, hl + 5, null, null, 'center');
    //        //             hl = hl + 10;
    //        // 
    //        //             var svg = this.nbCardContainer.nativeElement.querySelector('#divSocialscanEmail');
    //        //             var svg2 = svg.children[0].children[0].children[1].children[0].children[0].children[0];
    //        //             await html2canvas(svg2, { 
    //        //                 // scale: 1,
    //        //                 useCORS: true, 
    //        //                 // foreignObjectRendering: true,  // Render with the background but only if the div is in the screen
    //        //                 // logging: false,
    //        //                 backgroundColor: '#333333',
    //        //                 allowTaint: true,
    //        //                 // removeContainer: false
    //        //                 })
    //        //                 .then(function (canvas) { 
    //        //                     doc.addImage(canvas.toDataURL('image/png'), 'JPEG', 10, hl, 75, 55);
    //        //                 });
    //        // 
    //        //             doc.setFontSize(11);
    //        //             doc.setFont('helvetica', 'normal');
    //        //             doc.setTextColor(79, 79, 79);
    //        //             infoText = 'The information of the chart is shown in the following table.';
    //        //             var splitText = doc.splitTextToSize(infoText, 110);
    //        //             var y = 6;
    //        //             for (var i=0; i<splitText.length; i++){
    //        //                 doc.text(90, hl + y, splitText[i]);
    //        //                 y = y + 4;
    //        //             }
    //        // 
    //        //             // Information table
    //        //             if (this.gathered['socialscan']['result'][4]['graphic'][0]['social_email']) {
    //        //                 let headTable = [];
    //        //                 let bodyTable = [];
    //        //                 let elem = [];
    //        //                 let i: any;
    //        //                 let list = this.gathered['socialscan']['result'][4]['graphic'][0]['social_email'];
    //        //                 
    //        //                 for (let i in list) {
    //        //                     if (list[i]['title'] != 'SocialScan') {
    //        //                         elem = [list[i]['title']];
    //        //                         bodyTable.push(elem);
    //        //                     }
    //        //                 }
    //        // 
    //        //                 doc.autoTable({
    //        //                     startY: hl + 11,
    //        //                     margin: {left: 90},
    //        //                     showHead: true,
    //        //                     styles: { overflow: 'hidden' },
    //        //                     bodyStyles: {
    //        //                         fillColor: [52, 73, 94],
    //        //                         textColor: 240
    //        //                     },
    //        //                     alternateRowStyles: {
    //        //                         fillColor: [74, 96, 117]
    //        //                     },
    //        //                     head: [
    //        //                         ['SocialScan Email'],
    //        //                     ],
    //        //                     body: bodyTable,
    //        //                 });
    //        // 
    //        //                 let finalY = doc.previousAutoTable.finalY;
    //        //                 doc.autoTable({
    //        //                     startY: finalY,
    //        //                     // html: '.table',
    //        //                     useCss: true,
    //        //                 });
    //        //         
    //        //                 if (finalY >= hl + 55) {
    //        //                     hl = finalY;
    //        //                 } else {
    //        //                     hl = hl + 60;
    //        //                 }
    //        //             }
    //        // 
    //        //             hl = hl + 10;
    //        // 
    //        //             var svg = this.nbCardContainer.nativeElement.querySelector('#divSocialscanUser');
    //        //             var svg2 = svg.children[0].children[0].children[1].children[0].children[0].children[0];
    //        //             await html2canvas(svg2, { 
    //        //                 // scale: 1,
    //        //                 useCORS: true, 
    //        //                 // foreignObjectRendering: true,  // Render with the background but only if the div is in the screen
    //        //                 // logging: false,
    //        //                 backgroundColor: '#333333',
    //        //                 allowTaint: true,
    //        //                 // removeContainer: false
    //        //                 })
    //        //                 .then(function (canvas) { 
    //        //                     doc.addImage(canvas.toDataURL('image/png'), 'JPEG', 10, hl, 75, 55);
    //        //                 });
    //        // 
    //        //             doc.setFontSize(11);
    //        //             doc.setFont('helvetica', 'normal');
    //        //             doc.setTextColor(79, 79, 79);
    //        //             infoText = 'The information of the chart is shown in the following table.';
    //        //             var splitText = doc.splitTextToSize(infoText, 110);
    //        //             var y = 6;
    //        //             for (var i=0; i<splitText.length; i++){
    //        //                 doc.text(90, hl + y, splitText[i]);
    //        //                 y = y + 4;
    //        //             }
    //        // 
    //        //             // Information table
    //        //             if (this.gathered['socialscan']['result'][4]['graphic'][1]['social_user']) {
    //        //                 let headTable = [];
    //        //                 let bodyTable = [];
    //        //                 let elem = [];
    //        //                 let i: any;
    //        //                 let list = this.gathered['socialscan']['result'][4]['graphic'][1]['social_user'];
    //        //                 
    //        //                 for (let i in list) {
    //        //                     if (list[i]['title'] != 'SocialScan') {
    //        //                         elem = [list[i]['title']];
    //        //                         bodyTable.push(elem);
    //        //                     }
    //        //                 }
    //        // 
    //        //                 doc.autoTable({
    //        //                     startY: hl + 11,
    //        //                     margin: {left: 90},
    //        //                     showHead: true,
    //        //                     styles: { overflow: 'hidden' },
    //        //                     bodyStyles: {
    //        //                         fillColor: [52, 73, 94],
    //        //                         textColor: 240
    //        //                     },
    //        //                     alternateRowStyles: {
    //        //                         fillColor: [74, 96, 117]
    //        //                     },
    //        //                     head: [
    //        //                         ['SocialScan User'],
    //        //                     ],
    //        //                     body: bodyTable,
    //        //                 });
    //        // 
    //        //                 let finalY = doc.previousAutoTable.finalY;
    //        //                 doc.autoTable({
    //        //                     startY: finalY,
    //        //                     // html: '.table',
    //        //                     useCss: true,
    //        //                 });
    //        //         
    //        //                 hl = finalY
    //        //             }
    //        // 
    //        //             hl = hl + 10;
    //        //         }
    //        // 
    //        //         doc.addPage();
    //        //         hl = 20;
    //        //         // Profile
    //        //         for (let i in this.gathered) {
    //        //             console.log('i', i)
    //        //           for (let j in this.gathered[i]) {
    //        //             for (let k in this.gathered[i][j]) {
    //        //               for (let l in this.gathered[i][j][k]) {
    //        //                 if (l == 'profile') {
    //        //                   for (let p in this.gathered[i][j][k][l]) {
    //        //                     this.profile.push(this.gathered[i][j][k][l][p]);
    //        //                     for (let q in this.gathered[i][j][k][l][p]) {
    //        //                       switch(q) {
    //        //                         case 'name':
    //        //                         case 'firstName':
    //        //                         case 'lastName':
    //        //                           console.log('i', this.gathered[i][j][k][l][p][q]);
    //        //                           console.log('i prima', i)
    //        //                           if (this.gathered[i][j][k][l][p][q] != null) {
    //        //                               this.name.push({'label' : this.gathered[i][j][k][l][p][q], 'source' : i});
    //        //                           };
    //        //                           break;
    //        //                         case 'photos':
    //        //                           for (let iphoto in this.gathered[i][j][k][l][p][q]) {
    //        //                               this.photo.push(this.gathered[i][j][k][l][p][q][iphoto]);
    //        //                           };    
    //        //                           break;
    //        //                         case 'social':
    //        //                           for (let isocial in this.gathered[i][j][k][l][p][q]) {
    //        //                               this.social.push(this.gathered[i][j][k][l][p][q][isocial]);
    //        //                           };    
    //        //                           break;
    //        //                         case 'location':
    //        //                           this.location.push({'label' : this.gathered[i][j][k][l][p][q], 'source' : i});
    //        //                           break;
    //        //                         case 'organization':
    //        //                           if (Array.isArray(this.gathered[i][j][k][l][p][q])) {
    //        //                               for (let r in this.gathered[i][j][k][l][p][q]) {
    //        //                                   this.organization.push({'label' : this.gathered[i][j][k][l][p][q][r]['name'], 'source' : i});
    //        //                               }
    //        // 
    //        //                           } else {
    //        //                               this.organization.push({'label' : this.gathered[i][j][k][l][p][q], 'source' : i});
    //        //                           }    
    //        //                           break;
    //        //                         case 'gender':
    //        //                           this.gender.push({'label' : this.gathered[i][j][k][l][p][q], 'source' : i});
    //        //                           break;
    //        //                         default:
    //        //                           // code block
    //        //                       }
    //        //                     }
    //        //                   }
    //        //                 }
    //        //               }
    //        //             }
    //        //           }
    //        //         }     
    //        // 
    //        //         console.log('Profile name', this.name);
    //        //         console.log('Profile location', this.location);
    //        //         console.log('Profile gender', this.gender);
    //        //         console.log('Profile social', this.social);
    //        //         console.log('Profile photo', this.photo);
    //        //         console.log('Profile orgnization', this.organization);
    //        // 
    //        //         doc.setFontSize(11);
    //        //         doc.setDrawColor(32, 61, 79);
    //        //         doc.setFillColor(32, 61, 79);
    //        //         doc.rect(10, hl, 190, 7, 'F');
    //        //         doc.setTextColor(255, 255, 255);
    //        //         doc.text('Profile', 105, hl + 5, null, null, 'center');
    //        // 
    //        //         hl = 35;
    //        // 
    //        //         // Names
    //        //         if (this.name.length > 0) {
    //        //             let headTable = [];
    //        //             let bodyTable = [];
    //        //             let elem = [];
    //        //             let list = this.name;
    //        //             
    //        //             for (let i in list) {
    //        //                 elem = [list[i]['label'], list[i]['source']];
    //        //                 bodyTable.push(elem);
    //        //             }
    //        //             headTable = [['title']]
    //        //             headTable[0][0] = {content: 'Names', colSpan: 2, styles: {halign: 'center', fillColor: [22, 160, 133]}};
    //        //             doc.autoTable({
    //        //                 columnStyles: {0: {cellWidth: 50}},
    //        //                 startY: hl,
    //        //                 head: headTable, 
    //        //                 body: bodyTable,
    //        //             });
    //        //             let finalY = doc.previousAutoTable.finalY;
    //        //             hl = finalY;
    //        //         }
    //        //         // Gender
    //        //         if (this.gender.length > 0) {
    //        //             let headTable = [];
    //        //             let bodyTable = [];
    //        //             let elem = [];
    //        //             let list = this.gender;
    //        //             
    //        //             for (let i in list) {
    //        //                 elem = [list[i]['label'], list[i]['source']];
    //        //                 bodyTable.push(elem);
    //        //             }
    //        //             headTable = [['title']]
    //        //             headTable[0][0] = {content: 'Gender', colSpan: 2, styles: {halign: 'center', fillColor: [22, 160, 133]}};
    //        //             doc.autoTable({
    //        //                 columnStyles: {0: {cellWidth: 50}},
    //        //                 startY: hl,
    //        //                 head: headTable, 
    //        //                 body: bodyTable,
    //        //             });
    //        //             let finalY = doc.previousAutoTable.finalY;
    //        //             hl = finalY;
    //        //         }
    //        //         // Location
    //        //         if (this.location.length > 0) {
    //        //             let headTable = [];
    //        //             let bodyTable = [];
    //        //             let elem = [];
    //        //             let list = this.location;
    //        //             
    //        //             for (let i in list) {
    //        //                 elem = [list[i]['label'], list[i]['source']];
    //        //                 bodyTable.push(elem);
    //        //             }
    //        //             headTable = [['title']]
    //        //             headTable[0][0] = {content: 'Location', colSpan: 2, styles: {halign: 'center', fillColor: [22, 160, 133]}};
    //        //             doc.autoTable({
    //        //                 columnStyles: {0: {cellWidth: 50}},
    //        //                 startY: hl,
    //        //                 head: headTable, 
    //        //                 body: bodyTable,
    //        //             });
    //        //             let finalY = doc.previousAutoTable.finalY;
    //        //             hl = finalY;
    //        //         }
    //        //         // Organization
    //        //         if (this.organization.length > 0) {
    //        //             let headTable = [];
    //        //             let bodyTable = [];
    //        //             let elem = [];
    //        //             let list = this.organization;
    //        //             
    //        //             for (let i in list) {
    //        //                 elem = [list[i]['label'], list[i]['source']];
    //        //                 bodyTable.push(elem);
    //        //             }
    //        //             headTable = [['title']]
    //        //             headTable[0][0] = {content: 'Organization', colSpan: 2, styles: {halign: 'center', fillColor: [22, 160, 133]}};
    //        //             doc.autoTable({
    //        //                 columnStyles: {0: {cellWidth: 50}},
    //        //                 startY: hl,
    //        //                 head: headTable, 
    //        //                 body: bodyTable,
    //        //             });
    //        //             let finalY = doc.previousAutoTable.finalY;
    //        //             hl = finalY;
    //        //         }
    //        // 
    //        //         doc.addPage();
    //        //         hl = 20;
    //        //         // Timeline
    //        //         for (let i in this.gathered) {
    //        //           for (let j in this.gathered[i]) {
    //        //             for (let k in this.gathered[i][j]) {
    //        //               for (let l in this.gathered[i][j][k]) {
    //        //                 if (l == 'timeline') {
    //        //                   for (let t in this.gathered[i][j][k][l]) {
    //        //                     this.timeline.push(this.gathered[i][j][k][l][t]);
    //        //                   }
    //        //                 }
    //        //               }
    //        //             }
    //        //           }
    //        //         }     
    //        // 
    //        //         // TODO : Normalize dates
    //        //         this.timeline.sort(function(a, b){
    //        //             var dateA=a.date.toLowerCase(), dateB=b.date.toLowerCase()
    //        //             if (dateA > dateB) //sort string ascending
    //        //                 return -1 
    //        //             if (dateA < dateB)
    //        //                 return 1
    //        //             return 0 
    //        //         })
    //        // 
    //        //         doc.setFontSize(11);
    //        //         doc.setDrawColor(32, 61, 79);
    //        //         doc.setFillColor(32, 61, 79);
    //        //         doc.rect(10, hl, 190, 7, 'F');
    //        //         doc.setTextColor(255, 255, 255);
    //        //         doc.text('Timeline', 105, hl + 5, null, null, 'center');
    //        // 
    //        //         hl = 35;
    //        // 
    //        //         for (let i in this.timeline) {
    //        //             hl = hl + 5;
    //        //             doc.setFillColor(58, 127, 168);
    //        //             doc.setDrawColor(58, 127, 168);
    //        //             // doc.setTextColor(79, 79, 79);
    //        //             // doc.line(50, hl, 50, hl + 15);
    //        //             doc.circle(50, hl + 10, 2, 'F');
    //        //             // Information table
    //        //             let headTable = [[this.timeline[i]['date']]];
    //        //             let bodyTable = [[this.timeline[i]['action'] + ' - ' + [this.timeline[i]['desc']]]];
    //        // 
    //        //             doc.autoTable({
    //        //                 startY: hl + 10,
    //        //                 margin: {left: 60, right: 40},
    //        //                 showHead: true,
    //        //                 styles: { overflow: 'linebreak' },
    //        //                 bodyStyles: {
    //        //                     fillColor: [52, 73, 94],
    //        //                     textColor: 240
    //        //                 },
    //        //                 alternateRowStyles: {
    //        //                     fillColor: [74, 96, 117]
    //        //                 },
    //        //                 head: headTable,
    //        //                 body: bodyTable,
    //        //             });
    //        // 
    //        //             doc.setFillColor(58, 127, 168);
    //        //             doc.setDrawColor(58, 127, 168);
    //        //             doc.line(50, hl, 50, doc.previousAutoTable.finalY + 5);
    //        //             hl = doc.previousAutoTable.finalY;
    //        //             // Validate pageHeight
    //        //             if ( hl + 50 > pageHeight) {
    //        //                 doc.addPage();
    //        //                 hl = 20;
    //        //                 doc.setFontSize(11);
    //        //                 doc.setDrawColor(32, 61, 79);
    //        //                 doc.setFillColor(32, 61, 79);
    //        //                 doc.rect(10, hl, 190, 7, 'F');
    //        //                 doc.setTextColor(255, 255, 255);
    //        //                 doc.text('Timeline', 105, hl + 5, null, null, 'center');
    //        // 
    //        //                 hl = 35;
    //        //             }
    //        //         }
    //        // 
    //        //         // doc.text(this.timeline[i]['date'] + ' - ' + , 60, hl + 10, null, null, 'left');
    //        //         // hl = hl + 30;
    //        //         // TODO addPage
    //        //         
    //        doc.save('Report_iKy_' + this.gathered['email'] + '_' + Date.now() + '.pdf');
    //        this.processing = false;
    //    }
  cancelDownload(doc: any) {
    console.log('Cerrame la 9');
    doc.save('Report_iKy_' + Date.now() + '.pdf');
  }

}
