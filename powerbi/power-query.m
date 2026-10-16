// DataRoot: set to your local data/processed directory

// Orders
let
    Pointer = Json.Document(File.Contents(DataRoot & "/latest.json")),
    Contract = if Pointer[contract_version] = 1 then Pointer[snapshot] else error "Unsupported data contract",
    Source = Csv.Document(File.Contents(DataRoot & "/snapshots/" & Contract & "/Orders.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Headers, {{"Order ID", type text}, {"Purchase Date", type date}, {"State", type text}, {"Status", type text}, {"Delivered Date", type date}, {"Estimated Date", type date}, {"Item Count", Int64.Type}, {"Merchandise Cents", Int64.Type}, {"Freight Cents", Int64.Type}, {"Payment Cents", Int64.Type}, {"Payment Difference Cents", Int64.Type}, {"Delivery Eligible", Int64.Type}, {"Late", Int64.Type}, {"Delivery Days", Int64.Type}, {"Late Days", Int64.Type}, {"Delivery Band", type text}}, "en-US")
in
    Typed

// Items
let
    Pointer = Json.Document(File.Contents(DataRoot & "/latest.json")),
    Contract = if Pointer[contract_version] = 1 then Pointer[snapshot] else error "Unsupported data contract",
    Source = Csv.Document(File.Contents(DataRoot & "/snapshots/" & Contract & "/Items.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Headers, {{"Order ID", type text}, {"Item Number", Int64.Type}, {"Product ID", type text}, {"Purchase Date", type date}, {"State", type text}, {"Status", type text}, {"Category", type text}, {"Category Mapping", type text}, {"Price Cents", Int64.Type}, {"Freight Cents", Int64.Type}, {"Category Group", type text}}, "en-US")
in
    Typed

// Dates
let
    Pointer = Json.Document(File.Contents(DataRoot & "/latest.json")),
    Contract = if Pointer[contract_version] = 1 then Pointer[snapshot] else error "Unsupported data contract",
    Source = Csv.Document(File.Contents(DataRoot & "/snapshots/" & Contract & "/Dates.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Headers, {{"Date", type date}, {"Month", type text}, {"Year", Int64.Type}}, "en-US")
in
    Typed

// States
let
    Pointer = Json.Document(File.Contents(DataRoot & "/latest.json")),
    Contract = if Pointer[contract_version] = 1 then Pointer[snapshot] else error "Unsupported data contract",
    Source = Csv.Document(File.Contents(DataRoot & "/snapshots/" & Contract & "/States.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Headers, {{"State", type text}}, "en-US")
in
    Typed

// Categories
let
    Pointer = Json.Document(File.Contents(DataRoot & "/latest.json")),
    Contract = if Pointer[contract_version] = 1 then Pointer[snapshot] else error "Unsupported data contract",
    Source = Csv.Document(File.Contents(DataRoot & "/snapshots/" & Contract & "/Categories.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Headers, {{"Category", type text}}, "en-US")
in
    Typed

// Quality
let
    Pointer = Json.Document(File.Contents(DataRoot & "/latest.json")),
    Contract = if Pointer[contract_version] = 1 then Pointer[snapshot] else error "Unsupported data contract",
    Source = Csv.Document(File.Contents(DataRoot & "/snapshots/" & Contract & "/Quality.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Headers, {{"Check", type text}, {"Rows", Int64.Type}}, "en-US")
in
    Typed

// Refresh
let
    Pointer = Json.Document(File.Contents(DataRoot & "/latest.json")),
    Contract = if Pointer[contract_version] = 1 then Pointer[snapshot] else error "Unsupported data contract",
    Source = Csv.Document(File.Contents(DataRoot & "/snapshots/" & Contract & "/Refresh.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Headers, {{"Snapshot", type text}, {"Built UTC", type text}, {"Source Orders", Int64.Type}, {"Source Items", Int64.Type}, {"Exception Events", Int64.Type}, {"Orders With Exceptions", Int64.Type}}, "en-US")
in
    Typed
